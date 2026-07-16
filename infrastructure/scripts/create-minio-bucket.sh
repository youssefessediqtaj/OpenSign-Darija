#!/usr/bin/env sh
set -eu

mc alias set local "http://${MINIO_ENDPOINT:-minio:9000}" "${MINIO_ACCESS_KEY:-opensign}" "${MINIO_SECRET_KEY:-opensign_dev_password}"
mc mb --ignore-existing "local/${MINIO_BUCKET:-opensign-darija}"
