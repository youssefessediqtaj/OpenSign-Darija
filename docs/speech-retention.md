# Speech Retention

Defaults:

- guest audio TTL: 1 hour
- user audio TTL: 24 hours
- signed URL TTL: 15 minutes

Expired audio is cleaned with:

```bash
python -m app.jobs.cleanup_expired_audio
```

Deleting a message marks associated speech generations deleted and removes their audio object when available.
