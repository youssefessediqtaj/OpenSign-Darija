# Object Storage

MinIO stores raw dataset artifacts. PostgreSQL stores only metadata, checksums, object keys, and review state.

## Buckets

- `opensign-private-videos`
- `opensign-private-landmarks`
- `opensign-review-thumbnails`
- `opensign-dataset-exports`
- `opensign-reference-assets`

All uploaded videos are private. They are never made public automatically.

## Local URLs

The API uses `MINIO_ENDPOINT=minio:9000` for container-to-container access and `MINIO_PUBLIC_ENDPOINT=localhost:9000` when generating browser upload URLs in Docker development.

Run:

```bash
infrastructure/scripts/create-minio-bucket.sh
```

or rely on the API storage helper to create buckets during local upload/export operations.
