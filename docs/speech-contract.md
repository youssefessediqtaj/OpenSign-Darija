# Sign speech contract

Public request:

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
URL with duration/size. Unknown extra request fields and unsupported labels are rejected.
