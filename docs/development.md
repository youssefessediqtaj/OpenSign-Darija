# Development

## Full local verification

```bash
make install
make ml-install
make test
make compose-check
```

The frontend can be run alone with `npm run dev` from `apps/web`; set
`VITE_API_BASE_URL=http://localhost:8000` only for that standalone mode. Docker uses an
empty API base URL so browser requests stay same-origin through Nginx.

## Services

```bash
cd services/inference && .venv/bin/uvicorn app.main:app --reload --port 8001
cd services/speech && .venv/bin/uvicorn app.main:app --reload --port 8010
cd services/api && .venv/bin/uvicorn app.main:app --reload --port 8000
cd apps/web && npm run dev
```

Real inference needs the environment paths from `.env.example` and a validated local
package at `artifacts/models/mosl-isolated-sign-v1/`. The API is stateless and does not
run migrations or seed data. PostgreSQL, Redis, MinIO, user accounts, and object-storage
buckets are not part of the core development loop.
