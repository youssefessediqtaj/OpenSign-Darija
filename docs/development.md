# Development

## Frontend

```bash
cd apps/web
npm install
npm run dev
npm test -- --run
npm run build
```

## Backend

```bash
cd services/api
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

## Inference

```bash
cd services/inference
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8001
```

## MinIO Bucket

Apres demarrage Docker, creez le bucket local si necessaire:

```bash
docker compose exec minio sh /workspace/infrastructure/scripts/create-minio-bucket.sh
```

Phase 1 ne stocke pas encore de videos.
