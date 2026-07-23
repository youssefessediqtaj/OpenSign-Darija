# API log checklist

```bash
docker compose logs api
```

Expect only health/version, `/recognitions/word`, and `/speech/sign` traffic. Block on
tracebacks, DB/Redis/MinIO connection attempts, legacy routes returning non-404, payload
logging, repeated speech for one segment, or inference/speech dependency failures.
