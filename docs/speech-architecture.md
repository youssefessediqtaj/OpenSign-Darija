# Automatic sign speech

```text
known recognition -> browser sends supported label key
                  -> public API resolves package Arabic label
                  -> private offline speech service
                  -> playable WAV data URL
                  -> one automatic browser playback
```

UNKNOWN never reaches speech. The browser cannot submit arbitrary text and never calls
the speech container directly. The direct endpoint is stateless: no database, MinIO,
signed URL, cache worker, voice selector, message ownership, or finalized-message flow is
part of the recognition product.

The service tries its Darija-facing Arabic system voice first and the explicit Arabic
fallback second. If service audio generation or autoplay fails, browser Arabic speech is
attempted. All failure paths preserve visible recognized text and enter cooldown.
