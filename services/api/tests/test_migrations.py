import os
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_initial_migration_runs(tmp_path: Path) -> None:
    db_path = tmp_path / "migration.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")
    assert db_path.exists()
