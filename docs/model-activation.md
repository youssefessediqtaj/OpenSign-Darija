# Model Activation

Admin endpoints:

- `GET /api/v1/admin/models`
- `GET /api/v1/admin/models/{model_id}`
- `POST /api/v1/admin/models/{model_id}/validate`
- `POST /api/v1/admin/models/{model_id}/activate`
- `POST /api/v1/admin/models/{model_id}/archive`
- `POST /api/v1/admin/models/{model_id}/rollback`

Activation requires `READY` status and complete artifact metadata. The current implementation updates backend registry state; a future real artifact flow should add a hard warm-up call to inference before activation.
