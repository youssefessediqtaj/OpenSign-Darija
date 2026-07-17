# Speech Backend Log Checklist

Read logs for `api`, `speech`, `speech-worker`, `redis`, `minio`, `postgres` and `nginx`.

Look for:

- speech service unavailable
- invalid audio
- repeated generation for same request
- MinIO upload/signing failures
- cleanup failures
- HTTP 500 errors
- signed URLs or full text in logs
- Redis lock/cache failures once distributed locking is enabled
