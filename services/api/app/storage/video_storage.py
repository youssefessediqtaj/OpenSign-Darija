from __future__ import annotations

import os
import shutil
import tempfile
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import Protocol

from app.core.config import Settings


class VideoStorageError(RuntimeError):
    pass


class VideoStorage(Protocol):
    def health_check(self) -> bool: ...

    def create_staging_path(self, contribution_id: str) -> Path: ...

    def promote(self, staged_path: Path, object_key: str) -> None: ...

    def delete(self, object_key: str) -> None: ...

    def local_path(self, object_key: str) -> Path | None: ...

    def copy_to(self, object_key: str, destination: Path) -> None: ...


def _safe_object_key(object_key: str) -> PurePosixPath:
    key = PurePosixPath(object_key)
    if key.is_absolute() or ".." in key.parts or not key.parts:
        raise VideoStorageError("Unsafe generated contribution object key")
    return key


class LocalPrivateVideoStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.pending_root = self.root / "pending"
        self.staging_root = self.root / ".staging"

    def _prepare_directories(self) -> None:
        for directory in (self.root, self.pending_root, self.staging_root):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            directory.chmod(0o700)

    def health_check(self) -> bool:
        try:
            self._prepare_directories()
            descriptor, path = tempfile.mkstemp(prefix="health-", dir=self.staging_root)
            os.close(descriptor)
            Path(path).unlink()
            return True
        except OSError:
            return False

    def create_staging_path(self, contribution_id: str) -> Path:
        try:
            self._prepare_directories()
            descriptor, value = tempfile.mkstemp(
                prefix=f"{contribution_id}-",
                suffix=".upload",
                dir=self.staging_root,
            )
            os.close(descriptor)
            path = Path(value)
            path.chmod(0o600)
            return path
        except OSError as error:
            raise VideoStorageError("Private upload staging is unavailable") from error

    def _resolve(self, object_key: str) -> Path:
        key = _safe_object_key(object_key)
        resolved = self.root.joinpath(*key.parts).resolve()
        if self.root not in resolved.parents:
            raise VideoStorageError("Unsafe generated contribution object key")
        return resolved

    def promote(self, staged_path: Path, object_key: str) -> None:
        destination = self._resolve(object_key)
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination.parent.chmod(0o700)
        try:
            os.replace(staged_path, destination)
            destination.chmod(0o600)
        except OSError as error:
            raise VideoStorageError("Private video storage is unavailable") from error

    def delete(self, object_key: str) -> None:
        path = self._resolve(object_key)
        try:
            path.unlink(missing_ok=True)
            parent = path.parent
            if parent != self.root and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError as error:
            raise VideoStorageError("Private video deletion failed") from error

    def local_path(self, object_key: str) -> Path | None:
        return self._resolve(object_key)

    def copy_to(self, object_key: str, destination: Path) -> None:
        copy_private_file(self._resolve(object_key), destination)


class S3PrivateVideoStorage:
    """Private S3 adapter.

    It never generates a public URL or ACL. A temporary private key is copied to
    the final quarantine key before the local staged file is removed.
    """

    def __init__(self, settings: Settings):
        try:
            boto3 = import_module("boto3")
        except ImportError as error:  # pragma: no cover - dependency is production-only
            raise VideoStorageError("The S3 storage dependency is unavailable") from error
        if not settings.contribution_s3_bucket:
            raise VideoStorageError("The private S3 bucket is not configured")
        self.bucket = settings.contribution_s3_bucket
        self.prefix = settings.contribution_s3_prefix.strip("/")
        self.encryption = settings.contribution_s3_server_side_encryption
        self.staging_root = (settings.contribution_storage_root / ".staging").resolve()
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.contribution_s3_endpoint_url or None,
            region_name=settings.contribution_s3_region or None,
        )

    def _remote_key(self, object_key: str) -> str:
        safe = _safe_object_key(object_key).as_posix()
        return f"{self.prefix}/{safe}" if self.prefix else safe

    def health_check(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False

    def create_staging_path(self, contribution_id: str) -> Path:
        self.staging_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.staging_root.chmod(0o700)
        descriptor, value = tempfile.mkstemp(
            prefix=f"{contribution_id}-",
            suffix=".upload",
            dir=self.staging_root,
        )
        os.close(descriptor)
        path = Path(value)
        path.chmod(0o600)
        return path

    def promote(self, staged_path: Path, object_key: str) -> None:
        final_key = self._remote_key(object_key)
        temporary_key = f"{final_key}.staging"
        extra_args: dict[str, str] = {}
        if self.encryption:
            extra_args["ServerSideEncryption"] = self.encryption
        try:
            self.client.upload_file(
                str(staged_path),
                self.bucket,
                temporary_key,
                ExtraArgs=extra_args,
            )
            copy_source = {"Bucket": self.bucket, "Key": temporary_key}
            self.client.copy_object(
                Bucket=self.bucket,
                Key=final_key,
                CopySource=copy_source,
                **extra_args,
            )
            self.client.delete_object(Bucket=self.bucket, Key=temporary_key)
            staged_path.unlink(missing_ok=True)
        except Exception as error:
            try:
                self.client.delete_object(Bucket=self.bucket, Key=temporary_key)
            except Exception:
                pass
            raise VideoStorageError("Private object storage is unavailable") from error

    def delete(self, object_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=self._remote_key(object_key))
        except Exception as error:
            raise VideoStorageError("Private object deletion failed") from error

    def local_path(self, object_key: str) -> Path | None:
        return None

    def copy_to(self, object_key: str, destination: Path) -> None:
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.client.download_file(
                self.bucket,
                self._remote_key(object_key),
                str(destination),
            )
            destination.chmod(0o600)
        except Exception as error:
            destination.unlink(missing_ok=True)
            raise VideoStorageError("Private object download failed") from error


def build_video_storage(settings: Settings) -> VideoStorage:
    if settings.contribution_storage_backend == "local":
        return LocalPrivateVideoStorage(settings.contribution_storage_root)
    if settings.contribution_storage_backend == "s3":
        return S3PrivateVideoStorage(settings)
    raise VideoStorageError("Unsupported contribution storage backend")


def copy_private_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with source.open("rb") as input_stream, destination.open("xb") as output_stream:
        shutil.copyfileobj(input_stream, output_stream)
    destination.chmod(0o600)
