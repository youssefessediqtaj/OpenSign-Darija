# OpenSign Darija

OpenSign Darija est une application web open source visant a preparer la reconnaissance de signes de la Langue des Signes Marocaine, la construction de phrases en Darija et une future lecture vocale.

Phase actuelle: architecture, infrastructure et flux simule. La camera reelle, le dataset, le modele IA entraine et la synthese vocale ne sont pas encore inclus.

## Architecture

- `apps/web`: frontend React, TypeScript, Vite, Tailwind, TanStack Query, Zustand, i18next.
- `services/api`: API publique FastAPI, auth JWT/Argon2, SQLAlchemy, Alembic, PostgreSQL, Redis.
- `services/inference`: service FastAPI interne avec prediction mock compatible backend.
- `services/speech`: espace reserve pour une future synthese vocale.
- `ml`: espace reserve pour dataset, preprocessing, entrainement, evaluation et export.
- `infrastructure/nginx`: gateway public vers web et `/api`.

Le frontend ne contacte jamais directement le service d’inference.

## Prerequis

- Docker et Docker Compose
- Node.js 22 pour le developpement frontend manuel
- Python 3.12 pour le developpement backend/inference manuel

## Installation locale

```bash
cp .env.example .env
make install
```

Ne placez jamais de secrets reels dans `.env`.

## Demarrage Docker

```bash
docker compose up --build
```

Application via Nginx: `http://localhost:8080`

Services directs de developpement:

- Frontend container interne: `web:80`
- API: `http://localhost:8000`
- MinIO: `http://localhost:9001`

## Demarrage manuel

```bash
cd services/inference && uvicorn app.main:app --reload --port 8001
cd services/api && uvicorn app.main:app --reload --port 8000
cd apps/web && npm run dev
```

## Variables d’environnement

Copiez `.env.example` vers `.env`, puis ajustez les valeurs locales:

```bash
cp .env.example .env
```

Les variables principales couvrent PostgreSQL, Redis, MinIO, JWT, URL du service d’inference et `VITE_API_BASE_URL`.

## Base de donnees

```bash
make migrate
make seed
```

Le seeder cree les roles, six categories et dix signes de demonstration. Aucun compte demo n’est cree automatiquement.

## Tests

```bash
make test
make lint
```

Tests frontend seuls:

```bash
cd apps/web && npm test -- --run
cd apps/web && npm run test:e2e
```

Tests backend et inference:

```bash
cd services/api && pytest
cd services/inference && pytest
```

## Makefile

- `make install`: installe les dependances locales.
- `make dev`: demarre les services Docker principaux pour developpement.
- `make up`: construit et lance tout Docker Compose.
- `make down`: arrete Docker Compose.
- `make logs`: suit les logs.
- `make test`: execute les tests.
- `make lint`: execute les linters.
- `make format`: formate le code.
- `make migrate`: applique Alembic.
- `make seed`: charge les donnees initiales.
- `make clean`: supprime les artefacts locaux.

## Open Source Et Securite

Le code peut etre open source sous Apache-2.0. Les futurs datasets devront avoir leur propre licence. Les videos des contributeurs ne devront jamais devenir publiques automatiquement. Le produit ne remplace pas un interprete professionnel et ne doit pas etre presente comme medicalement ou juridiquement certifie.

Voir `CONTRIBUTING.md`, `SECURITY.md` et `docs/security.md`.

## Roadmap

Voir `docs/roadmap.md`.
