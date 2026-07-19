PYTHON ?= python3

.PHONY: install dev up down logs logs-api logs-worker logs-storage test test-backend test-frontend test-dataset test-e2e test-browser lint format migrate seed seed-dataset seed-linguistics dataset-build dataset-validate dataset-validate-training dataset-stats dataset-prepare dataset-download-kaggle-alphabet dataset-import-mendeley dataset-audit-external dataset-build-alphabet dataset-build-mosl-words dataset-map-labels dataset-validate-licenses dataset-check-duplicates dataset-extract-word-landmarks train-alphabet evaluate-alphabet export-alphabet-onnx train-external-words evaluate-external-words test-external-datasets test-recognition-modes test-browser-alphabet logs-datasets ml-install ml-download-mediapipe ml-inventory-nested-mosl ml-verify-mosl-migration ml-final-deletion-verification ml-dataset-import ml-dataset-scan ml-dataset-validate ml-dataset-split ml-preprocess-mosl ml-validate-mosl-artifacts ml-prepare-word-training-manifest ml-train-smoke ml-validate-word-smoke-model ml-register-word-smoke-model ml-activate-word-smoke ml-train-word ml-evaluate-word ml-export-word ml-package-word ml-register-word-model model-list model-activate model-rollback inference-test test-ml test-inference test-recognition-e2e test-linguistics test-messages-backend test-messages-frontend test-messages-e2e test-browser-messages message-demo linguistic-export linguistic-validate logs-messages benchmark-inference cleanup-uploads speech-install speech-download-model speech-verify-model speech-test speech-test-backend speech-test-frontend speech-test-e2e speech-benchmark speech-cleanup speech-voices speech-health logs-speech clean

install:
	cd apps/web && npm install
	cd services/api && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd services/inference && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd services/speech && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev:
	docker compose up postgres redis minio inference api web

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	@echo "No worker service is configured yet; cleanup jobs run through the API image."

logs-storage:
	docker compose logs -f minio

test:
	$(MAKE) test-frontend
	$(MAKE) test-backend
	$(MAKE) test-inference
	cd services/speech && .venv/bin/pytest

test-backend:
	cd services/api && .venv/bin/python -m pytest
	cd services/api && .venv/bin/ruff check app tests
	cd services/api && .venv/bin/mypy app

test-frontend:
	cd apps/web && npm test -- --run
	cd apps/web && npm run lint

test-dataset: test-backend

test-e2e:
	cd apps/web && npm run test:e2e

test-browser: test-e2e

lint:
	cd apps/web && npm run lint
	cd services/api && ruff check app tests && mypy app
	cd services/inference && ruff check app tests && mypy app

format:
	cd apps/web && npm run format
	cd services/api && ruff format app tests
	cd services/inference && ruff format app tests

migrate:
	cd services/api && alembic upgrade head

seed:
	cd services/api && .venv/bin/python -m app.db.seed

seed-dataset: seed

seed-linguistics: seed

dataset-build:
	$(PYTHON) -m ml.datasets.build_manifest

dataset-validate:
	$(PYTHON) -m ml.datasets.validate_dataset

dataset-validate-training:
	$(PYTHON) -m ml.datasets.validate_training_dataset --dataset-version 0.1.0

dataset-stats:
	$(PYTHON) -m ml.datasets.generate_statistics

dataset-prepare:
	$(PYTHON) -m ml.preprocessing.prepare_sequences

dataset-download-kaggle-alphabet:
	$(PYTHON) -m ml.datasets.external.download_kaggle --dataset walidlasseg/moroccan-sign-language-lsm-alphabet-dataset --output data/raw/external/kaggle-lsm-alphabet

dataset-import-mendeley:
	$(PYTHON) -m ml.datasets.external.download_mendeley --dataset-id 23phgyt3mt --version 1 --output data/raw/external/mendeley-mosl-v1

dataset-audit-external:
	$(PYTHON) -m ml.datasets.external.audit --root data/raw/external --output data/reports

dataset-build-alphabet:
	$(PYTHON) -m ml.datasets.alphabet.manifest_builder
	$(PYTHON) -m ml.datasets.alphabet.split_builder

dataset-build-mosl-words:
	$(PYTHON) -m ml.datasets.mosl_words.manifest_builder
	$(PYTHON) -m ml.datasets.mosl_words.validator

dataset-map-labels:
	@echo "Use /admin/datasets/external/alphabet-labels and /admin/datasets/external/word-labels for human mapping."

dataset-validate-licenses:
	$(PYTHON) -m ml.datasets.external.validate_licenses

dataset-check-duplicates:
	$(PYTHON) -m ml.datasets.external.check_duplicates

ml-download-mediapipe:
	$(PYTHON) -m ml.datasets.mosl_video.download_mediapipe_model

ml-inventory-nested-mosl:
	@test -n "$(MOSL_SOURCE_ROOT)" || { echo "Set MOSL_SOURCE_ROOT to the local source project root."; exit 2; }
	$(PYTHON) -m ml.datasets.mosl_video.source_inventory --source-root "$(MOSL_SOURCE_ROOT)"

ml-verify-mosl-migration:
	@test -n "$(MOSL_SOURCE_DATASET_ROOT)" || { echo "Set MOSL_SOURCE_DATASET_ROOT to the local source video root."; exit 2; }
	$(PYTHON) -m ml.datasets.mosl_video.migration_verification --source-root "$(MOSL_SOURCE_DATASET_ROOT)"

ml-final-deletion-verification:
	$(PYTHON) -m ml.datasets.mosl_video.final_deletion_verification $(if $(MOSL_VALIDATION_SUMMARY),--validation-summary "$(MOSL_VALIDATION_SUMMARY)",)

ml-install:
	$(PYTHON) -m venv ml/.venv
	ml/.venv/bin/python -m pip install --upgrade pip
	ml/.venv/bin/python -m pip install -r ml/requirements-train.txt

ml-dataset-import:
	@test -n "$(MOSL_SOURCE_DATASET_ROOT)" || { echo "Set MOSL_SOURCE_DATASET_ROOT to the local source video root."; exit 2; }
	$(PYTHON) -m ml.datasets.mosl_video.importer --source "$(MOSL_SOURCE_DATASET_ROOT)"

ml-dataset-scan:
	$(PYTHON) -m ml.datasets.mosl_video.scan

ml-dataset-validate: ml-dataset-scan

ml-dataset-split:
	$(PYTHON) -m ml.datasets.mosl_video.split_builder

ml-preprocess-mosl:
	services/inference/.venv/bin/python -m ml.datasets.mosl_video.preprocess

ml-validate-mosl-artifacts:
	services/inference/.venv/bin/python -m ml.datasets.mosl_video.validate_processed_artifacts

ml-prepare-word-training-manifest:
	$(PYTHON) -m ml.datasets.mosl_video.training_manifest

ml-train-smoke:
	$(MAKE) ml-prepare-word-training-manifest
	ml/.venv/bin/python -m ml.training.train_mosl_word --manifest artifacts/datasets/mosl-word-isolated-v1/manifest.json --output-dir artifacts/models/mosl-word-smoke-v1 --epochs 2

ml-validate-word-smoke-model:
	ml/.venv/bin/python -m ml.export.validate_mosl_word_smoke --artifact-dir artifacts/models/mosl-word-smoke-v1

ml-register-word-smoke-model: ml-validate-word-smoke-model
	cd services/api && PYTHONPATH=.:../.. .venv/bin/python -m app.tools.register_mosl_word_smoke --artifact-dir ../../artifacts/models/mosl-word-smoke-v1

ml-activate-word-smoke: ml-validate-word-smoke-model
	cd services/api && PYTHONPATH=.:../.. .venv/bin/python -m app.tools.activate_mosl_word_smoke --artifact-dir ../../artifacts/models/mosl-word-smoke-v1

ml-train-word:
	$(PYTHON) -m ml.training.train --config ml/configs/mosl-word-isolated-baseline-v1.yaml --dataset-version source-import-v1 --output-dir ml/artifacts/mosl-word-gru-v1/full

ml-evaluate-word:
	$(PYTHON) -m ml.evaluation.evaluate --artifact-dir ml/artifacts/mosl-word-gru-v1/full

ml-export-word:
	$(PYTHON) -m ml.export.export_onnx --checkpoint ml/artifacts/mosl-word-gru-v1/full/model.pt --output ml/artifacts/mosl-word-gru-v1/full/model.onnx

ml-package-word:
	$(PYTHON) -m ml.export.package_model --artifact-dir ml/artifacts/mosl-word-gru-v1/full

ml-register-word-model: ml-register-word-smoke-model

dataset-extract-word-landmarks:
	$(PYTHON) -m ml.datasets.mosl_words.landmark_extractor --source mendeley_mosl_v1 --feature-schema 1.0.0 --target-frames 30

train-alphabet:
	@echo "Alphabet training is blocked until Kaggle license and labels are verified."

evaluate-alphabet:
	@echo "No alphabet model metrics exist until training is run on a verified dataset."

export-alphabet-onnx:
	@echo "No alphabet ONNX export exists until a verified alphabet model is trained."

train-external-words:
	@echo "External word training requires audited Mendeley videos, approved labels, and selected vocabulary."

evaluate-external-words:
	@echo "No external word metrics exist until training is run."

test-external-datasets:
	PYTHONPATH=. $(PYTHON) -m pytest ml/tests/test_external_datasets.py

test-recognition-modes:
	cd services/api && ./.venv/bin/pytest tests/test_recognition_modes.py

test-browser-alphabet:
	cd apps/web && npm run test:e2e -- alphabet.spec.ts

logs-datasets:
	docker compose logs -f api inference nginx minio

ml-baseline:
	$(PYTHON) -m ml.training.train_baseline --dataset-version 0.1.0

ml-train:
	$(PYTHON) -m ml.training.train --config ml/configs/gru.yaml --dataset-version 0.1.0

ml-evaluate:
	$(PYTHON) -m ml.evaluation.evaluate --artifact-dir ml/artifacts/opensign-pilot-gru/0.1.0

ml-export-onnx:
	$(PYTHON) -m ml.export.export_onnx --checkpoint ml/artifacts/opensign-pilot-gru/0.1.0/model.pt --output ml/artifacts/opensign-pilot-gru/0.1.0/model.onnx

ml-validate-onnx:
	$(PYTHON) -m ml.export.validate_onnx --checkpoint ml/artifacts/opensign-pilot-gru/0.1.0/model.pt --onnx ml/artifacts/opensign-pilot-gru/0.1.0/model.onnx

ml-register-model:
	$(PYTHON) -m ml.export.register_model --artifact-dir ml/artifacts/opensign-pilot-gru/0.1.0

model-list:
	curl -sS http://localhost:8081/api/v1/models/active

model-activate:
	@test -n "$(MODEL_ID)" || (echo "Usage: make model-activate MODEL_ID=<id>" && exit 1)
	@test -n "$(TOKEN)" || (echo "Usage: make model-activate MODEL_ID=<id> TOKEN=<admin-jwt>" && exit 1)
	curl -sS -X POST -H "Authorization: Bearer $(TOKEN)" http://localhost:8081/api/v1/admin/models/$(MODEL_ID)/activate

model-rollback:
	@test -n "$(MODEL_ID)" || (echo "Usage: make model-rollback MODEL_ID=<id>" && exit 1)
	@test -n "$(TOKEN)" || (echo "Usage: make model-rollback MODEL_ID=<id> TOKEN=<admin-jwt>" && exit 1)
	curl -sS -X POST -H "Authorization: Bearer $(TOKEN)" http://localhost:8081/api/v1/admin/models/$(MODEL_ID)/rollback

inference-test test-inference:
	cd services/inference && .venv/bin/pytest
	cd services/inference && .venv/bin/ruff check app tests
	cd services/inference && .venv/bin/mypy app

test-ml:
	PYTHONPATH=. services/inference/.venv/bin/pytest ml/tests

test-recognition-e2e:
	cd apps/web && npm run test:e2e -- recognition-camera.spec.ts

test-linguistics:
	cd services/api && ./.venv/bin/pytest tests/test_messages_linguistics.py

test-messages-backend: test-linguistics

test-messages-frontend:
	cd apps/web && npm test -- --run src/features/messages/tests/components.test.tsx

test-messages-e2e:
	cd apps/web && npm run test:e2e -- messages.spec.ts

test-browser-messages: test-messages-e2e

message-demo:
	curl -sS http://localhost:8081/api/v1/linguistics/version

linguistic-export:
	curl -sS http://localhost:8081/api/v1/linguistics/concepts

linguistic-validate: test-linguistics

logs-messages:
	docker compose logs -f api speech nginx

speech-install:
	cd services/speech && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

speech-download-model:
	@echo "No external speech model is downloaded in phase 6 MVP; local provider has no bundled weights."

speech-verify-model:
	cd services/speech && .venv/bin/python -c "from app.providers.registry import ProviderRegistry; assert ProviderRegistry().ready(); print('speech model metadata verified')"

speech-test:
	cd services/speech && .venv/bin/pytest
	cd services/speech && .venv/bin/ruff check app tests
	cd services/speech && .venv/bin/mypy app

speech-test-backend:
	cd services/api && .venv/bin/pytest tests/test_speech_audio.py

speech-test-frontend:
	cd apps/web && npm test -- --run src/features/speech/tests/speech-player.test.tsx

speech-test-e2e:
	cd apps/web && npm run test:e2e -- messages.spec.ts

speech-benchmark:
	$(PYTHON) scripts/benchmark_speech.py

speech-cleanup:
	docker compose exec -T api python -m app.jobs.cleanup_expired_audio

speech-voices:
	curl -sS http://localhost:8081/api/v1/speech/voices

speech-health:
	curl -sS http://localhost:8081/api/v1/speech/status && echo
	docker compose exec -T speech python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8010/ready').read().decode())"

logs-speech:
	docker compose logs -f speech speech-worker api nginx

benchmark-inference:
	$(PYTHON) scripts/benchmark_inference.py

cleanup-uploads:
	docker compose exec -T api python -m app.jobs.cleanup_orphan_uploads

clean:
	rm -rf apps/web/dist apps/web/coverage services/api/.pytest_cache services/inference/.pytest_cache
