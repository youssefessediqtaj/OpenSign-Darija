# MoSL Source Audit

Date: 2026-07-19

## Scope

This audit inspects the existing OpenSigne Darija monorepo and the local source folder `Multimodal-Moroccan-Sign-Language-Generation` before integration. The audit is the gate for integration work; the source application is not treated as authoritative architecture.

## Existing OpenSigne Darija Architecture

OpenSigne Darija is a single monorepo with these boundaries:

- `apps/web`: React/Vite frontend. Browser camera capture and MediaPipe landmark extraction happen locally.
- `services/api`: public FastAPI backend under `/api/v1`, with auth, recognition sessions, dataset metadata, model registry, message building, speech orchestration, PostgreSQL, Redis, and MinIO clients.
- `services/inference`: internal FastAPI inference service. Nginx does not expose it publicly.
- `services/speech`: internal speech service. Nginx does not expose it publicly.
- `ml`: native scripts for dataset manifests, external dataset gates, preprocessing placeholders, training/evaluation/export scaffolding, and tests.
- `infrastructure/nginx`: public web and `/api` gateway.
- `docker-compose.yml`: authoritative service graph for web, api, inference, speech, speech-worker, postgres, redis, minio, nginx.

The frontend never calls inference or speech directly. Raw recognition camera video/images/audio are not sent to the backend.

## Existing ML Folder Structure

Relevant native ML folders:

- `ml/datasets`: local manifest, validation, split and statistics utilities.
- `ml/datasets/external`: external source registry, archive safety, license validation, audit and duplicate checks.
- `ml/datasets/alphabet`: separate alphabet dataset import/manifest/split helpers.
- `ml/datasets/mosl_words`: separate word-video manifest, label, signer and validation helpers.
- `ml/preprocessing`: normalization, masking, sampling, feature selection, augmentation, sequence preparation.
- `ml/models`: baseline and GRU classifier scaffolding.
- `ml/training`: training entrypoints and config helpers.
- `ml/evaluation`: metrics, calibration, unknown detection and report utilities.
- `ml/export`: ONNX export, validation, packaging and model registration scaffolding.
- `ml/tests`: ML and external dataset tests.

## Existing Recognition Contracts

Frontend canonical constants are currently in `apps/web/src/features/recognition/services/landmark-normalizer.service.ts`.

Current browser/API/inference request contract:

- `feature_schema_version`: `1.0.0`
- `coordinate_format`: `torso_normalized_v1`
- sequence length: 1-60 compact frames
- per-frame features: 63 floats
- per-frame presence mask: 21 integers
- landmarks represented: 6 pose points, 3 face points, 6 selected left-hand points, 6 selected right-hand points
- privacy: compact normalized landmarks only; no raw video/image/audio

Current API schemas are in `services/api/app/schemas/recognition.py`. Current inference schemas are in `services/inference/app/schemas/prediction.py`.

Current inference response contract returns request/model metadata, `feature_schema_version`, `inference_mode`, decision/confidence level, Top-K predictions, unknown probability, and processing time.

## Existing Model Registry And Storage

`services/api/app/models/sign.py` defines `ModelVersion` with `task_type`, `input_modality`, `feature_schema_version`, `source_dataset_versions`, `supported_classes`, `labels_json`, metrics, thresholds, artifact path/checksum/size, and active/validation/archive timestamps.

Admin APIs in `services/api/app/api/v1/admin_models.py` validate, activate, archive and roll back registered models. Activation is explicit and per recognition task type. Current inference real mode loads local ONNX artifacts through `services/inference/app/models/onnx_model.py` and fails closed when `MODEL_PATH` or labels are missing.

Model artifacts are intended to remain private, with MinIO configured through `MODEL_BUCKET=opensign-model-artifacts`.

## Existing External Dataset Tables And APIs

`services/api/app/models/dataset.py` includes `ExternalDatasetSource`, `ExternalDatasetImport`, and `ExternalDatasetLabel`. Admin external dataset APIs are under `/api/v1/admin/external-datasets`.

The existing architecture stores metadata in PostgreSQL and large binary artifacts outside PostgreSQL. Existing source registry docs and scripts already separate public external sources and license gates.

## Existing Test Frameworks

- Frontend: Vitest, ESLint, TypeScript build, Playwright.
- API: pytest, Ruff, MyPy, Alembic migration tests.
- Inference: pytest, Ruff, MyPy.
- Speech: pytest, Ruff, MyPy.
- ML: pytest via `PYTHONPATH=.`.
- Docker: `docker compose config`, service health checks, Nginx runtime checks.

## External Project Tree

Local root: `Multimodal-Moroccan-Sign-Language-Generation`.

Source commit SHA: `bfae9b378cdf6eaed7f2f20b16297b281e9f7eca`.

Important inspected files and folders:

- `README.md`: minimal title only.
- `requirements.txt`
- `mosl_classification.py`
- `mosl_complete.py`
- `mosl_kaggle_classification.ipynb`
- `mosl_signllm_complete.ipynb`
- `signllm_mosl_kaggle.py`
- `signllm_mosl_kaggle.ipynb`
- `Dockerfile`
- `docker-compose.yml`
- `DOCKER.md`
- `.dockerignore`
- `.devcontainer/devcontainer.json`
- `.devcontainer/A dataset for Moroccan sign language recognition and translation.pdf`
- `.devcontainer/SignLLM- Sign Language.pdf`
- `output/confusion_matrix.png`
- `output/dataset_distribution.png`
- `output/mosl_cnn_model.pth`
- `output/training_curves.png`
- `signllm_mosl_project/README.md`
- `signllm_mosl_project/config.yaml`
- `signllm_mosl_project/requirements.txt`
- `signllm_mosl_project/mosl_utils.py`
- `signllm_mosl_project/mosl_model.py`
- `signllm_mosl_project/mosl_rl_loss.py`
- `signllm_mosl_project/run_pipeline.py`
- `signllm_mosl_project/notebooks/01_analyze_dataset.ipynb` through `08_full_pipeline.ipynb`
- `signllm_mosl_project/outputs/landmarks/*.npy`
- Python caches and agent/devcontainer artifacts.

Dataset root: `Multimodal-Moroccan-Sign-Language-Generation/vedios-dataset` (source spelling preserved here for provenance).

## External Dataset Folders

| Folder | Target mode | Videos | Size |
|---|---:|---:|---:|
| `mosl_videos_dataset_Diverse` | `WORD_ISOLATED` | 1,941 | 240M |
| `mosl_videos_dataset_Letters` | `ALPHABET_STATIC` | 71 | 5.7M |
| `mosl_videos_dataset_Numbers` | `WORD_ISOLATED` | 130 | 14M |
| `mosl_videos_dataset_Pronouns` | `WORD_ISOLATED` | 15 | 1.3M |
| `mosl_videos_dataset_days_months_seasons` | `WORD_ISOLATED` | 59 | 6.6M |

Total videos: 2,216.

Total dataset size: 284M by `du -sh`.

Non-video files: one `.DS_Store`.

Video readability has not yet been fully validated at audit time; `ffprobe`, `ffmpeg`, OpenCV and MediaPipe are available locally, and the native scanner must record per-file readability before migration is considered complete.

## Useful Source Components

Useful as technical reference only:

- Full MP4 dataset and Arabic filenames.
- Category folder names.
- MediaPipe body/hand landmark extraction idea.
- Landmark caching as `.npy`.
- Dataset inventory/splitting idea.
- Baseline classification/evaluation examples.
- Confusion matrix/classification report examples.

## Rejected Source Components

Not migrated into active OpenSigne runtime:

- SignLLM text-to-pose pipeline.
- AraBERT/text encoders.
- Prompt2LangGloss.
- RL loss and Priority Learning Channel for generated poses.
- Generated skeletal sign video/avatar demos.
- BLEU/ROUGE evaluation for generated sign poses.
- Duplicate frontend/backend/Docker/Compose files.
- Jupyter notebooks as production runtime.
- Generated outputs (`output/*`, `signllm_mosl_project/outputs/*`).
- Python caches, `.venv`, `.devcontainer`, local agent files.
- External application wiring and source-specific absolute-path assumptions.

## Files To Migrate

The dataset videos under `vedios-dataset/` are candidates for local migration into `ml/data/external/mosl-video-dataset/raw/`.

No large source code file is approved for verbatim migration because the local source folder contains no explicit source-code license file.

## Files Not To Migrate

All external app code, notebooks, duplicate Docker files, generated model/checkpoint/images, generated `.npy` caches, Python caches, `.venv`, `.devcontainer`, and agent files are not migrated to production folders.

## Licensing And Provenance

No `LICENSE`, `LICENSE.md`, or `COPYING` file was found in the local source project. Source-code license status: `UNCONFIRMED`; do not copy substantial code verbatim.

The external project README references Ben Zaid et al., “A MoSL dataset”, Data in Brief 64 (2026). Earlier OpenSigne documentation records Mendeley MoSL v1 DOI `10.17632/23phgyt3mt.1` as CC BY 4.0, but the local copied dataset itself does not include a standalone license file. Dataset license status for this local folder remains `UNCONFIRMED` until confirmed against source metadata and citation docs in the integration docs. Raw videos must stay private/local and out of the public frontend bundle.

## Integration Risks

- Current OpenSigne schema is 21 landmarks/63 values per frame; the requested source-derived schema is 75 landmarks/225 values per frame. This is a deliberate schema migration, not a small parameter change.
- Full MediaPipe preprocessing of 2,216 videos may take substantial time on CPU.
- PyTorch is not installed in the current inference virtualenv; smoke/full training requires optional ML dependencies.
- Signer identity is not evident from local filenames; signer-independent split may be impossible without source metadata.
- Many classes may have one or two samples, so training eligibility must be conservative.
- Source code license is unconfirmed, so implementation must be native and independently written.
- Dataset license for the local copy must be treated as restricted/research-only until verified.

## Final Target Architecture

Target architecture remains native OpenSigne:

`Browser camera -> local MediaPipe landmarks -> public FastAPI API -> internal inference service -> ONNX model -> API recognition session -> user confirmation/correction -> Darija message -> speech`.

Dataset integration target:

- `ml/data/external/mosl-video-dataset/raw/*` for local raw videos.
- `ml/data/external/mosl-video-dataset/manifests/*` for manifest/checksum/category/label summaries.
- `ml/data/external/mosl-video-dataset/processed/*` for cached canonical landmark sequences.
- `ml/data/external/mosl-video-dataset/splits/*` for reproducible mode-separated splits.
- `ml/data/external/mosl-video-dataset/reports/*` for validation, preprocessing, training and evaluation reports.
- `ml/data/external/mosl-video-dataset/quarantine/*` only for manually confirmed unusable artifacts.

`WORD_ISOLATED` and `ALPHABET_STATIC` remain separate through dataset manifests, splits, training, model registry and inference routing.
