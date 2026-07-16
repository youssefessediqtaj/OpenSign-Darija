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
