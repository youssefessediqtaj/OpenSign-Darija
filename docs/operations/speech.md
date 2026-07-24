# Automatic sign speech

The speech path exists only after a known recognition result:

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

## Public contract

```http
POST /api/v1/speech/sign
Content-Type: application/json

{"label_key":"سوق"}
```

Only a key present in the active model package is accepted. The API owns the Arabic text
mapping and sends the private service a bounded synthesis request with locale `ar-MA`,
voice `darija-default`, speed `1.0`, and WAV output. It retries with locale `ar` and
`arabic-fallback` only after a provider error.

The compact response contains the label, completion state, fallback flag, and WAV data
URL with duration and size. Unknown extra request fields and unsupported labels are
rejected.

## Offline providers

`local-darija` and `local-arabic-fallback` use the same installed system speech engine;
their distinction makes preferred vs fallback locale explicit. macOS uses `say -v Majed`
and Docker installs `espeak-ng -v ar`. Arguments are passed directly without a shell.

No voice weights, text, or audio are sent to an external provider. Temporary WAV files
are deleted immediately after validation. The providers are experimental and must not be
described as native Moroccan voices or used for cloning/impersonation.

## Browser fallback

When service WAV playback cannot start, the active recognition loop tries
`window.speechSynthesis` with an Arabic voice (`ar-MA`, then `ar`). This is automatic
because camera activation is the originating user gesture. Browser and operating-system
voice availability vary.

If both paths fail, the Arabic result remains visible, `Audio indisponible` is shown,
and the optional repeat action can retry. Failure never converts a recognized result to
an error or causes duplicate automatic speech.

## Security and privacy

- browser input is a supported label key, not free text;
- API resolves and validates the Arabic label from the checksummed model package;
- service input length, speed, voice, and output format are validated;
- synthesis uses an argument array without a shell;
- no microphone permission or recording exists;
- no remote TTS request, account, token, DB row, object-storage object, or persistent
  cache is created;
- logs must never include WAV/base64 bodies or full request payloads.
