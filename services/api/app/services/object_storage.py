from datetime import timedelta
from typing import Any, cast

from app.core.config import get_settings

PRIVATE_VIDEO_BUCKET = "opensign-private-videos"
PRIVATE_LANDMARK_BUCKET = "opensign-private-landmarks"
THUMBNAIL_BUCKET = "opensign-review-thumbnails"
DATASET_EXPORT_BUCKET = "opensign-dataset-exports"
REFERENCE_ASSET_BUCKET = "opensign-reference-assets"
MODEL_ARTIFACT_BUCKET = "opensign-model-artifacts"
SPEECH_AUDIO_BUCKET = "opensign-speech-audio"
SPEECH_MODEL_BUCKET = "opensign-speech-models"

DATASET_BUCKETS = [
    PRIVATE_VIDEO_BUCKET,
    PRIVATE_LANDMARK_BUCKET,
    THUMBNAIL_BUCKET,
    DATASET_EXPORT_BUCKET,
    REFERENCE_ASSET_BUCKET,
    MODEL_ARTIFACT_BUCKET,
    SPEECH_AUDIO_BUCKET,
    SPEECH_MODEL_BUCKET,
]


class ObjectStorage:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, endpoint: str) -> Any:
        from minio import Minio  

        return Minio(
            endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
            region="us-east-1",
        )

    def ensure_buckets(self) -> None:
        client = self._client(self.settings.minio_endpoint)
        for bucket in DATASET_BUCKETS:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)

    def presigned_put_url(self, bucket: str, object_key: str, content_type: str) -> str:
        try:
            self.ensure_buckets()
            client = self._client(self.settings.minio_public_endpoint)
            return cast(
                str,
                client.presigned_put_object(
                    bucket,
                    object_key,
                    expires=timedelta(seconds=self.settings.dataset_presigned_url_expire_seconds),
                ),
            )
        except Exception:
            if self.settings.app_env == "production":
                raise
            return (
                f"http://{self.settings.minio_public_endpoint}/{bucket}/{object_key}"
                f"?X-Amz-Expires={self.settings.dataset_presigned_url_expire_seconds}"
                f"&content-type={content_type}"
            )

    def presigned_get_url(self, bucket: str, object_key: str) -> str:
        try:
            client = self._client(self.settings.minio_public_endpoint)
            return cast(
                str,
                client.presigned_get_object(
                    bucket,
                    object_key,
                    expires=timedelta(seconds=self.settings.dataset_presigned_url_expire_seconds),
                ),
            )
        except Exception:
            if self.settings.app_env == "production":
                raise
            return (
                f"http://{self.settings.minio_public_endpoint}/{bucket}/{object_key}"
                f"?X-Amz-Expires={self.settings.dataset_presigned_url_expire_seconds}"
            )

    def presigned_speech_get_url(self, object_key: str) -> str:
        bucket = self.settings.speech_audio_bucket
        try:
            client = self._client(self.settings.minio_public_endpoint)
            return cast(
                str,
                client.presigned_get_object(
                    bucket,
                    object_key,
                    expires=timedelta(seconds=self.settings.speech_signed_url_ttl_seconds),
                ),
            )
        except Exception:
            if self.settings.app_env == "production":
                raise
            return (
                f"http://{self.settings.minio_public_endpoint}/{bucket}/{object_key}"
                f"?X-Amz-Expires={self.settings.speech_signed_url_ttl_seconds}"
            )

    def put_text(self, bucket: str, object_key: str, content: str, content_type: str) -> None:
        try:
            import io

            encoded = content.encode("utf-8")
            self.ensure_buckets()
            client = self._client(self.settings.minio_endpoint)
            client.put_object(
                bucket, object_key, io.BytesIO(encoded), len(encoded), content_type=content_type
            )
        except Exception:
            if self.settings.app_env == "production":
                raise

    def put_bytes(self, bucket: str, object_key: str, content: bytes, content_type: str) -> None:
        try:
            import io

            self.ensure_buckets()
            client = self._client(self.settings.minio_endpoint)
            client.put_object(
                bucket, object_key, io.BytesIO(content), len(content), content_type=content_type
            )
        except Exception:
            if self.settings.app_env == "production":
                raise

    def delete_object(self, bucket: str, object_key: str) -> None:
        try:
            client = self._client(self.settings.minio_endpoint)
            client.remove_object(bucket, object_key)
        except Exception:
            if self.settings.app_env == "production":
                raise


def recording_object_prefix(
    campaign_id: str, anonymous_id: str, contribution_id: str, recording_id: str
) -> str:
    return (
        f"campaigns/{campaign_id}/contributors/{anonymous_id}/contributions/"
        f"{contribution_id}/recordings/{recording_id}"
    )
