# Speech Contract

Phase 6 genere un audio experimental local pour les messages finalises.

Service interne:

```json
{
  "text": "بغيت الما",
  "language": "ary-MA",
  "voice_id": "darija-default",
  "speed": 1.0,
  "output_format": "wav"
}
```

Endpoints publics principaux:

- `GET /api/v1/speech/voices`
- `GET /api/v1/speech/status`
- `POST /api/v1/messages/{message_id}/speech`
- `GET /api/v1/messages/{message_id}/speech/{generation_id}`
- `POST /api/v1/messages/{message_id}/speech/{generation_id}/refresh-url`
- `DELETE /api/v1/messages/{message_id}/speech/{generation_id}`

Le service speech reste interne au reseau Docker.
