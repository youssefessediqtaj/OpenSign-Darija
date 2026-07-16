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

## Dataset Contribution

- `GET /api/v1/consents/templates`
- `GET /api/v1/consents/me`
- `POST /api/v1/consents`
- `POST /api/v1/consents/{consent_id}/revoke`
- `GET /api/v1/contributors/me`
- `POST /api/v1/contributors/me`
- `PATCH /api/v1/contributors/me`
- `GET /api/v1/contribution-campaigns`
- `GET /api/v1/contribution-campaigns/{campaign_id}`
- `GET /api/v1/contribution-campaigns/{campaign_id}/signs`
- `POST /api/v1/contributions`
- `GET /api/v1/contributions/me`
- `GET /api/v1/contributions/{contribution_id}`
- `PATCH /api/v1/contributions/{contribution_id}`
- `DELETE /api/v1/contributions/{contribution_id}`
- `POST /api/v1/contributions/{contribution_id}/recordings`
- `GET /api/v1/contributions/{contribution_id}/recordings`
- `DELETE /api/v1/contributions/{contribution_id}/recordings/{recording_id}`
- `POST /api/v1/contributions/{contribution_id}/recordings/{recording_id}/upload-session`
- `POST /api/v1/contributions/{contribution_id}/recordings/{recording_id}/confirm-upload`
- `POST /api/v1/contributions/{contribution_id}/submit`
- `POST /api/v1/contributions/{contribution_id}/revoke`

## Reviews

- `GET /api/v1/reviews/linguistic/queue`
- `GET /api/v1/reviews/linguistic/{contribution_id}`
- `POST /api/v1/reviews/linguistic/{contribution_id}/decision`
- `GET /api/v1/reviews/ml/queue`
- `GET /api/v1/reviews/ml/{contribution_id}`
- `POST /api/v1/reviews/ml/{contribution_id}/decision`

Linguistic review requires `LINGUIST_REVIEWER` or `ADMIN`. ML review requires `ML_REVIEWER` or `ADMIN`.

## Admin Dataset Versions

- `GET /api/v1/admin/datasets`
- `POST /api/v1/admin/datasets`
- `GET /api/v1/admin/datasets/{dataset_version_id}`
- `POST /api/v1/admin/datasets/{dataset_version_id}/build`
- `POST /api/v1/admin/datasets/{dataset_version_id}/validate`
- `POST /api/v1/admin/datasets/{dataset_version_id}/publish`
- `POST /api/v1/admin/datasets/{dataset_version_id}/archive`

Admin exports include approved, non-revoked, upload-confirmed recordings only. Export manifests use anonymous contributor IDs and must not include email or auth user IDs.

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
