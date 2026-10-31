from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class ContributionRepositoryError(RuntimeError):
    pass


class DuplicateContributionError(ContributionRepositoryError):
    pass


SCHEMA_VERSION = 1
VALID_REVIEW_STATES = {
    "PENDING",
    "REJECTED",
    "APPROVED_FOR_DATASET",
}
VALID_DELETION_STATES = {
    "ACTIVE",
    "WITHDRAWAL_REQUESTED",
    "DELETED",
}


class ContributionRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path.resolve()

    def _prepare_parent(self) -> None:
        self.database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.database_path.parent.chmod(0o700)

    def connect(self) -> sqlite3.Connection:
        try:
            self._prepare_parent()
            connection = sqlite3.connect(self.database_path, timeout=5)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA journal_mode = WAL")
            self._migrate(connection)
            if self.database_path.exists():
                self.database_path.chmod(0o600)
            return connection
        except (OSError, sqlite3.Error) as error:
            raise ContributionRepositoryError("Contribution metadata is unavailable") from error

    def _migrate(self, connection: sqlite3.Connection) -> None:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise ContributionRepositoryError("Contribution database schema is newer than this API")
        if version == 0:
            connection.executescript(
                """
                CREATE TABLE contributors (
                    contribution_id TEXT PRIMARY KEY,
                    full_name TEXT,
                    age INTEGER,
                    city TEXT,
                    consent_version TEXT NOT NULL,
                    consent_timestamp TEXT NOT NULL,
                    controller_notice_version TEXT NOT NULL,
                    deletion_status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE contribution_videos (
                    contribution_id TEXT PRIMARY KEY
                        REFERENCES contributors(contribution_id) ON DELETE RESTRICT,
                    sign_key TEXT NOT NULL,
                    private_object_key TEXT NOT NULL UNIQUE,
                    sha256 TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    frame_rate REAL,
                    review_status TEXT NOT NULL DEFAULT 'PENDING',
                    processing_eligibility INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE contribution_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contribution_id TEXT NOT NULL
                        REFERENCES contributors(contribution_id) ON DELETE RESTRICT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX idx_contribution_review_status
                    ON contribution_videos(review_status, created_at);
                CREATE INDEX idx_contribution_deletion_status
                    ON contributors(deletion_status, created_at);
                PRAGMA user_version = 1;
                """
            )
            connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if "sha256" in str(error) or "UNIQUE" in str(error):
                raise DuplicateContributionError("Duplicate contribution video") from error
            raise ContributionRepositoryError("Contribution metadata commit failed") from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def health_check(self) -> bool:
        try:
            with self.connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except ContributionRepositoryError:
            return False

    def insert(
        self,
        connection: sqlite3.Connection,
        *,
        contribution_id: str,
        full_name: str,
        age: int,
        city: str,
        consent_version: str,
        consent_timestamp: str,
        sign_key: str,
        private_object_key: str,
        sha256: str,
        mime_type: str,
        file_size_bytes: int,
        duration_seconds: float,
        width: int,
        height: int,
        frame_rate: float | None,
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO contributors (
                contribution_id, full_name, age, city, consent_version,
                consent_timestamp, controller_notice_version, deletion_status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """,
            (
                contribution_id,
                full_name,
                age,
                city,
                consent_version,
                consent_timestamp,
                consent_version,
                created_at,
                created_at,
            ),
        )
        connection.execute(
            """
            INSERT INTO contribution_videos (
                contribution_id, sign_key, private_object_key, sha256, mime_type,
                file_size_bytes, duration_seconds, width, height, frame_rate,
                review_status, processing_eligibility, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?, ?)
            """,
            (
                contribution_id,
                sign_key,
                private_object_key,
                sha256,
                mime_type,
                file_size_bytes,
                duration_seconds,
                width,
                height,
                frame_rate,
                created_at,
                created_at,
            ),
        )
        self._event(connection, contribution_id, "RECEIVED", "public-api", None, created_at)

    def _event(
        self,
        connection: sqlite3.Connection,
        contribution_id: str,
        event_type: str,
        actor: str,
        reason: str | None,
        created_at: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO contribution_events (
                contribution_id, event_type, actor, reason, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                contribution_id,
                event_type,
                actor,
                reason,
                created_at or datetime.now(UTC).isoformat(),
            ),
        )

    def get_receipt(self, contribution_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT v.contribution_id, v.sign_key, v.created_at,
                       c.consent_version, v.review_status
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.contribution_id = ?
                """,
                (contribution_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_for_review(self, contribution_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT v.contribution_id, v.sign_key, v.private_object_key, v.sha256,
                       v.mime_type, v.file_size_bytes, v.duration_seconds, v.width,
                       v.height, v.frame_rate, v.review_status,
                       v.processing_eligibility, v.created_at, c.age, c.city,
                       c.consent_version, c.consent_timestamp, c.deletion_status
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.contribution_id = ?
                """,
                (contribution_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_pending(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT v.contribution_id, v.sign_key, v.duration_seconds, v.width,
                       v.height, v.created_at, c.deletion_status
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.review_status = 'PENDING' AND c.deletion_status = 'ACTIVE'
                ORDER BY v.created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def transition_review(
        self,
        contribution_id: str,
        target: str,
        *,
        actor: str,
        reason: str | None = None,
    ) -> bool:
        if target not in VALID_REVIEW_STATES:
            raise ValueError("Invalid review state")
        now = datetime.now(UTC).isoformat()
        with self.transaction() as connection:
            current = connection.execute(
                """
                SELECT v.review_status, c.deletion_status
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.contribution_id = ?
                """,
                (contribution_id,),
            ).fetchone()
            if not current:
                return False
            if current["deletion_status"] != "ACTIVE":
                raise ContributionRepositoryError(
                    "Withdrawn or deleted contributions cannot be reviewed"
                )
            connection.execute(
                """
                UPDATE contribution_videos
                SET review_status = ?, processing_eligibility = ?, updated_at = ?
                WHERE contribution_id = ?
                """,
                (target, int(target == "APPROVED_FOR_DATASET"), now, contribution_id),
            )
            self._event(connection, contribution_id, target, actor, reason, now)
        return True

    def request_withdrawal(self, contribution_id: str, *, actor: str) -> bool:
        now = datetime.now(UTC).isoformat()
        with self.transaction() as connection:
            result = connection.execute(
                """
                UPDATE contributors
                SET deletion_status = 'WITHDRAWAL_REQUESTED', updated_at = ?
                WHERE contribution_id = ? AND deletion_status = 'ACTIVE'
                """,
                (now, contribution_id),
            )
            if result.rowcount:
                connection.execute(
                    """
                    UPDATE contribution_videos
                    SET processing_eligibility = 0, updated_at = ?
                    WHERE contribution_id = ?
                    """,
                    (now, contribution_id),
                )
                self._event(
                    connection,
                    contribution_id,
                    "WITHDRAWAL_REQUESTED",
                    actor,
                    None,
                    now,
                )
        return bool(result.rowcount)

    def mark_deleted(self, contribution_id: str, *, actor: str, reason: str) -> bool:
        now = datetime.now(UTC).isoformat()
        with self.transaction() as connection:
            result = connection.execute(
                """
                UPDATE contributors
                SET full_name = NULL, age = NULL, city = NULL,
                    deletion_status = 'DELETED', updated_at = ?
                WHERE contribution_id = ? AND deletion_status != 'DELETED'
                """,
                (now, contribution_id),
            )
            if result.rowcount:
                connection.execute(
                    """
                    UPDATE contribution_videos
                    SET processing_eligibility = 0, updated_at = ?
                    WHERE contribution_id = ?
                    """,
                    (now, contribution_id),
                )
                self._event(connection, contribution_id, "DELETED", actor, reason, now)
        return bool(result.rowcount)

    def list_exportable(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT v.contribution_id, v.sign_key, v.private_object_key, v.sha256,
                       v.mime_type, v.file_size_bytes, v.duration_seconds, v.width,
                       v.height, v.frame_rate, v.review_status, v.created_at,
                       c.consent_version, c.consent_timestamp, c.deletion_status
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.review_status = 'APPROVED_FOR_DATASET'
                  AND v.processing_eligibility = 1
                  AND c.deletion_status = 'ACTIVE'
                ORDER BY v.contribution_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def retention_candidates(self, retention_days: int) -> list[dict[str, Any]]:
        cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT v.contribution_id, v.sign_key, v.private_object_key,
                       v.review_status, c.deletion_status, v.created_at
                FROM contribution_videos v
                JOIN contributors c USING (contribution_id)
                WHERE v.created_at < ?
                  AND (
                    v.review_status IN ('PENDING', 'REJECTED')
                    OR c.deletion_status = 'WITHDRAWAL_REQUESTED'
                  )
                  AND c.deletion_status != 'DELETED'
                ORDER BY v.created_at
                """,
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]


def secure_database_files(database_path: Path) -> None:
    for path in (
        database_path,
        Path(f"{database_path}-wal"),
        Path(f"{database_path}-shm"),
    ):
        if path.exists():
            os.chmod(path, 0o600)
