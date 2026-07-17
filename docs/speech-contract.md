# Speech Contract

Phase 5 ne genere aucun audio.

Contrat prepare:

```json
{
  "message_id": "uuid",
  "text": "بغيت الما",
  "language": "ary-MA",
  "voice": "default",
  "speed": 1.0
}
```

L'endpoint API `POST /api/v1/messages/{message_id}/speech/prepare` et le service `speech` retournent `not_implemented`.
