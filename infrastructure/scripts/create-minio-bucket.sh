#!/usr/bin/env sh
set -eu

mc alias set local "http://${MINIO_ENDPOINT:-minio:9000}" "${MINIO_ACCESS_KEY:-opensign}" "${MINIO_SECRET_KEY:-opensign_dev_password}"
mc mb --ignore-existing "local/${MINIO_PRIVATE_VIDEO_BUCKET:-opensign-private-videos}"
mc mb --ignore-existing "local/${MINIO_PRIVATE_LANDMARK_BUCKET:-opensign-private-landmarks}"
mc mb --ignore-existing "local/${MINIO_THUMBNAIL_BUCKET:-opensign-review-thumbnails}"
mc mb --ignore-existing "local/${MINIO_DATASET_EXPORT_BUCKET:-opensign-dataset-exports}"
mc mb --ignore-existing "local/${MINIO_REFERENCE_ASSET_BUCKET:-opensign-reference-assets}"
mc mb --ignore-existing "local/${MINIO_MODEL_ARTIFACT_BUCKET:-opensign-model-artifacts}"
