# Speech Cache

Conceptual cache key:

```text
speech:{sha256(normalized_text_hash:voice_id:speed:format:model_version)}
```

The backend currently prevents duplicate generation by finding an unexpired completed generation for the same message text hash, voice, speed and format, then reuses its MinIO object URL. Redis is reserved for distributed locks, metadata TTL and rate limiting as the asynchronous worker is expanded.

Audio bytes are never stored in Redis.
