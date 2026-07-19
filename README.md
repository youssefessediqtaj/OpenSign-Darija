# OpenSign Darija

OpenSign Darija est une application web open source visant a preparer la reconnaissance de signes de la Langue des Signes Marocaine, la construction de phrases en Darija et une future lecture vocale.

Phase actuelle: camera web reelle avec extraction locale de landmarks, plateforme MVP de collecte dataset, infrastructure phase 4 pour le premier modele reel, et constructeur de messages Darija controle. Aucun modele reel n’est entraine ni actif tant que le dataset local n’est pas valide.

## Architecture

- `apps/web`: frontend React, TypeScript, Vite, Tailwind, TanStack Query, Zustand, i18next.
- `services/api`: API publique FastAPI, auth JWT/Argon2, SQLAlchemy, Alembic, PostgreSQL, Redis.
- `services/inference`: service FastAPI interne avec prediction mock compatible backend.
- `services/speech`: service interne de synthese vocale experimentale avec provider local, normalisation Darija et fallback arabe explicite.
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
make dataset-validate-licenses
make dataset-download-kaggle-alphabet
make dataset-import-mendeley
make dataset-audit-external
make dataset-build-alphabet
make dataset-build-mosl-words
make dataset-check-duplicates
make cleanup-uploads
```

Dataset video MoSL local integre:

```bash
MOSL_SOURCE_DATASET_ROOT=/path/to/source/videos make ml-dataset-import
make ml-dataset-scan
make ml-dataset-split
make ml-install
make ml-download-mediapipe
make ml-preprocess-mosl
make ml-validate-mosl-artifacts
make ml-validate-word-smoke-model
```

Les videos brutes sont conservees localement sous `ml/data/external/mosl-video-dataset/raw/` et restent hors Git. Le modele MoSL actuel est un smoke model developpement seulement, pas un modele production. Voir `docs/datasets/mosl-video-dataset.md`, `docs/integrations/mosl-integration.md`, `docs/integrations/nested-mosl-removal-plan.md`, `docs/ml/landmark-schema-v1.md`, `docs/ml/mosl-preprocessing.md` et `docs/reports/mosl-native-integration-final-report.md`.

Sources publiques externes:

- Kaggle `walidlasseg/moroccan-sign-language-lsm-alphabet-dataset`: source `ALPHABET_STATIC`, desactivee tant que la licence officielle Kaggle n’est pas verifiee.
- Mendeley Data `10.17632/23phgyt3mt.1`: source `WORD_ISOLATED`, licence CC BY 4.0.
- ScienceDirect `10.1016/j.dib.2025.112395`: reference documentaire du dataset Mendeley, non comptee comme dataset distinct.

Les credentials Kaggle restent hors Git via `KAGGLE_USERNAME`, `KAGGLE_KEY` ou `~/.kaggle/kaggle.json`. Les archives, images, videos, landmarks volumineux, modeles et credentials restent hors Git sous `data/`.

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
- `make seed-linguistics`: charge concepts, mappings, dictionnaire et templates de demonstration.
- `make dataset-build`: construit un manifeste local.
- `make dataset-validate`: valide le manifeste local.
- `make dataset-prepare`: prepare un index de sequences.
- `make dataset-stats`: calcule les statistiques locales.
- `make dataset-validate-licenses`: verifie les gates de licence et la non-duplication ScienceDirect/Mendeley.
- `make dataset-download-kaggle-alphabet`: recupere les metadonnees Kaggle et bloque si la licence est absente/incompatible.
- `make dataset-import-mendeley`: prepare l'import Mendeley; utilisez ensuite `import_local_archive` avec l'archive locale.
- `make dataset-audit-external`: produit les rapports d'audit structurel externes.
- `make dataset-build-alphabet`: construit un manifest alphabet separe.
- `make dataset-build-mosl-words`: construit un manifest video mots separe.
- `make dataset-check-duplicates`: detecte les doublons inter-sources.
- `make ml-dataset-import`: importe le dataset video MoSL local vers la structure native; requiert `MOSL_SOURCE_DATASET_ROOT`.
- `make ml-verify-mosl-migration`: verifie les checksums source/native; requiert `MOSL_SOURCE_DATASET_ROOT`.
- `make ml-inventory-nested-mosl`: inventorie une source locale; requiert `MOSL_SOURCE_ROOT`.
- `make ml-dataset-scan`: regenere les manifestes video MoSL.
- `make ml-dataset-split`: genere les splits separes word/alphabet.
- `make ml-install`: cree `ml/.venv` avec les dependances PyTorch/ONNX de training, separees du runtime inference.
- `make ml-download-mediapipe`: installe le modele MediaPipe Tasks requis pour le preprocessing local.
- `make ml-preprocess-mosl`: extrait les landmarks MediaPipe vers des caches `.npz`.
- `make ml-validate-mosl-artifacts`: valide les caches `.npz` contre le manifeste.
- `make ml-validate-word-smoke-model`: valide le package ONNX smoke MoSL.
- `make ml-register-word-smoke-model`: enregistre le smoke model sans l'activer.
- `make ml-activate-word-smoke`: active le smoke model uniquement si `APP_ENV=development` et `ALLOW_SMOKE_MODEL_ACTIVATION=true`.
- `make ml-final-deletion-verification`: produit le rapport de gate avant toute suppression du projet source imbrique.
- `make dataset-validate-training`: refuse l’entrainement si le dataset n’est pas valide.
- `make ml-baseline`: entraine la baseline quand le dataset est valide.
- `make ml-train`: lance l’entrainement GRU quand le dataset est valide.
- `make ml-evaluate`: lit les metriques d’artefact.
- `make ml-export-onnx`: exporte un checkpoint valide en ONNX.
- `make ml-validate-onnx`: valide checksum/parite ONNX.
- `make ml-register-model`: verifie un dossier d’artefacts modele.
- `make model-list`: affiche le modele actif public.
- `make inference-test`: teste le service inference.
- `make test-ml`: lance les tests ML synthétiques.
- `make test-linguistics`: teste le moteur linguistique controle.
- `make test-messages-backend`: teste les endpoints messages.
- `make test-messages-frontend`: teste les composants messages.
- `make test-messages-e2e`: teste le parcours navigateur messages.
- `make logs-messages`: suit les logs API, speech et Nginx.
- `make speech-test`: teste le service speech.
- `make speech-health`: verifie le statut speech via Nginx et le service interne.
- `make speech-cleanup`: nettoie les audios speech expires.
- `make benchmark-inference`: mesure 20 appels inference locaux.
- `make cleanup-uploads`: dry-run de nettoyage des uploads orphelins.
- `make clean`: supprime les artefacts locaux.

## Open Source Et Securite

Le code peut etre open source sous Apache-2.0. Les futurs datasets devront avoir leur propre licence. Les videos des contributeurs ne devront jamais devenir publiques automatiquement. Le produit ne remplace pas un interprete professionnel et ne doit pas etre presente comme medicalement ou juridiquement certifie.

Voir `CONTRIBUTING.md`, `SECURITY.md` et `docs/security.md`.

## Roadmap

Voir `docs/roadmap.md`.

## Camera Et Confidentialite

La page `/app/recognition` demande explicitement l’autorisation camera. MediaPipe Holistic extrait visage, mains et haut du corps dans le navigateur. Aucune video, image, capture canvas ou audio n’est envoyee au backend. Seuls des landmarks compacts et normalises sont transmis a `POST /api/v1/recognitions`.

Le modele de reconnaissance reste en mode mock par defaut (`INFERENCE_MODE=mock`). En `INFERENCE_MODE=real`, le service inference exige un artefact ONNX valide et retourne 503 si le modele est absent.

La page `/app/recognition` propose deux modes separes: reconnaissance de signe isole et alphabet/epellation. L'epellation construit un mot lettre par lettre avec confirmation; elle n'est pas presentee comme une traduction complete.

## Modele IA

Voir `MODEL_CARD.md` et:

- `docs/model-training.md`
- `docs/model-evaluation.md`
- `docs/signer-independent-testing.md`
- `docs/unknown-detection.md`
- `docs/model-calibration.md`
- `docs/onnx-export.md`
- `docs/model-registry.md`
- `docs/model-activation.md`
- `docs/inference-service.md`

## Messages Darija

La page `/app/messages` permet de construire un message depuis des signes confirmes, des mots manuels marques comme tels, un moteur linguistique deterministe et une edition finale separee.

Documentation:

- `docs/message-builder.md`
- `docs/semantic-concepts.md`
- `docs/linguistic-engine.md`
- `docs/darija-writing-conventions.md`
- `docs/darija-latin-conventions.md`
- `docs/message-history.md`
- `docs/message-privacy.md`
- `docs/speech-contract.md`
- `docs/speech-architecture.md`
- `docs/speech-provider.md`
- `docs/browser-speech-fallback.md`
- `SPEECH_MODEL_CARD.md`

## Consentements Dataset

Le flux dataset separe les consentements landmarks, stockage, video, recherche, entrainement et publication. Aucune case n’est pre-cochee. Les videos restent privees et ne sont jamais publiees automatiquement. Les exports utilisent des identifiants contributeurs anonymes et ne doivent pas contenir email ni `user_id`.
