# API

## Systeme

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/version`

## Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

## Signes

- `GET /api/v1/signs?page=1&page_size=20&search=&category=`
- `GET /api/v1/signs/{sign_id}`
- `GET /api/v1/categories`

## Reconnaissance

- `POST /api/v1/recognitions/mock`
- `POST /api/v1/recognitions`
- `POST /api/v1/recognitions/{recognition_id}/confirm`
- `POST /api/v1/recognitions/{recognition_id}/correct`

`POST /api/v1/recognitions` accepts compact normalized landmark sequences only. It does not accept images, video, audio, or raw camera frames.

Format d’erreur:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Les donnees envoyees sont invalides.",
    "details": {}
  }
}
```
