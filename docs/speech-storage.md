# Speech Storage

Speech audio uses private bucket:

```text
opensign-speech-audio
```

Object layout:

```text
speech/{year}/{month}/{generation_id}/audio.wav
```

Paths do not include message text, email, names or session identifiers. The API returns temporary MinIO signed URLs with `SPEECH_SIGNED_URL_TTL_SECONDS`.

The frontend must not persist signed URLs or audio files in `localStorage`.
