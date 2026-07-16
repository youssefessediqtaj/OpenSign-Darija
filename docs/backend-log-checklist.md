# Backend Log Checklist

Use these commands while testing dataset collection:

```bash
make logs-api
make logs-storage
```

Check for:

- `403 CONSENT_REQUIRED` when required consent is missing.
- `403 VIDEO_CONSENT_REQUIRED` when a video upload is requested without video consent.
- `403 FORBIDDEN` for reviewer/admin endpoints with the wrong role.
- Successful `POST /api/v1/contributions/{id}/submit`.
- Successful review decisions.
- Successful admin dataset build and validation.

Unexpected stack traces or object-storage errors should block dataset publication.
