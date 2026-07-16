# OpenSign Darija

OpenSign Darija est une application web open source visant a preparer la reconnaissance de signes de la Langue des Signes Marocaine, la construction de phrases en Darija et une future lecture vocale.

Phase actuelle: camera web reelle avec extraction locale de landmarks pour la reconnaissance, plus une plateforme MVP de collecte dataset avec consentements, profils contributeurs, reviews, stockage MinIO et exports manifestes. Le modele IA entraine, la synthese vocale et la capture camera reelle integree au flux dataset ne sont pas encore inclus.

## Architecture

- `apps/web`: frontend React, TypeScript, Vite, Tailwind, TanStack Query, Zustand, i18next.
- `services/api`: API publique FastAPI, auth JWT/Argon2, SQLAlchemy, Alembic, PostgreSQL, Redis.
- `services/inference`: service FastAPI interne avec prediction mock compatible backend.
- `services/speech`: espace reserve pour une future synthese vocale.
- `ml`: scripts de manifestes dataset, validation, statistiques, preparation de sequences, et espaces reserves pour entrainement/evaluation.
- `infrastructure/nginx`: gateway public vers web et `/api`.

Le frontend ne contacte jamais directement le service d’inference.

## Prerequis

- Docker et Docker Compose
- Node.js 22 pour le developpement frontend manuel
- Python 3.12 pour le developpement backend/inference manuel
- Navigateur compatible camera (`localhost` ou HTTPS hors local)

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

Application via Nginx: `http://localhost:8081`

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

Le seeder cree les roles, six categories, dix signes de demonstration, une campagne pilote, les templates de consentement et les comptes de developpement suivants. Mot de passe local: `OpenSignDemo123!`.

- `contributor@example.test`
- `linguist@example.test`
- `ml-reviewer@example.test`
- `admin@example.test`

## Tests

```bash
make test
make lint
make test-dataset
```

Tests frontend seuls:

```bash
cd apps/web && npm test -- --run
cd apps/web && npm run test:e2e
cd apps/web && npm run perf:recognition
```

Tests backend et inference:

```bash
cd services/api && pytest
cd services/inference && pytest
```

## Dataset

Pages principales:

- `/app/contribute/consent`
- `/app/contribute/campaigns`
- `/app/contribute/history`
- `/admin/reviews/linguistic`
- `/admin/reviews/ml`
- `/admin/datasets`

Commandes dataset:

```bash
make seed-dataset
make dataset-build
make dataset-validate
make dataset-prepare
make dataset-stats
make cleanup-uploads
```

Documentation:

- `DATASET_CARD.md`
- `docs/dataset-collection.md`
- `docs/consent-management.md`
- `docs/contribution-workflow.md`
- `docs/review-workflow.md`
- `docs/object-storage.md`
- `docs/dataset-versioning.md`
- `docs/dataset-export.md`
- `docs/manual-browser-testing.md`

## Makefile

- `make install`: installe les dependances locales.
- `make dev`: demarre les services Docker principaux pour developpement.
- `make up`: construit et lance tout Docker Compose.
- `make down`: arrete Docker Compose.
- `make logs`: suit les logs.
- `make logs-api`: suit les logs API.
- `make logs-storage`: suit les logs MinIO.
- `make test`: execute les tests.
- `make test-backend`: execute pytest, Ruff et MyPy API.
- `make test-frontend`: execute Vitest et lint frontend.
- `make test-e2e`: execute Playwright.
- `make test-dataset`: alias des tests backend dataset.
- `make lint`: execute les linters.
- `make format`: formate le code.
- `make migrate`: applique Alembic.
- `make seed`: charge les donnees initiales.
- `make seed-dataset`: charge les donnees initiales et dataset.
- `make dataset-build`: construit un manifeste local.
- `make dataset-validate`: valide le manifeste local.
- `make dataset-prepare`: prepare un index de sequences.
- `make dataset-stats`: calcule les statistiques locales.
- `make cleanup-uploads`: dry-run de nettoyage des uploads orphelins.
- `make clean`: supprime les artefacts locaux.

## Open Source Et Securite

Le code peut etre open source sous Apache-2.0. Les futurs datasets devront avoir leur propre licence. Les videos des contributeurs ne devront jamais devenir publiques automatiquement. Le produit ne remplace pas un interprete professionnel et ne doit pas etre presente comme medicalement ou juridiquement certifie.

Voir `CONTRIBUTING.md`, `SECURITY.md` et `docs/security.md`.

## Roadmap

Voir `docs/roadmap.md`.

## Camera Et Confidentialite

La page `/app/recognition` demande explicitement l’autorisation camera. MediaPipe Holistic extrait visage, mains et haut du corps dans le navigateur. Aucune video, image, capture canvas ou audio n’est envoyee au backend. Seuls des landmarks compacts et normalises sont transmis a `POST /api/v1/recognitions`.

Le modele de reconnaissance est encore simule.

## Consentements Dataset

Le flux dataset separe les consentements landmarks, stockage, video, recherche, entrainement et publication. Aucune case n’est pre-cochee. Les videos restent privees et ne sont jamais publiees automatiquement. Les exports utilisent des identifiants contributeurs anonymes et ne doivent pas contenir email ni `user_id`.
