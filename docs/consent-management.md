# Consent Management

Consent is explicit and separate. No consent checkbox should be preselected.

## Consent Types

- `LANDMARK_PROCESSING`
- `LANDMARK_STORAGE`
- `VIDEO_RECORDING`
- `VIDEO_STORAGE`
- `RESEARCH_USE`
- `MODEL_TRAINING`
- `PUBLIC_DATASET_RELEASE`
- `COMMERCIAL_USE`

Landmark contribution requires landmark processing, landmark storage, research use, and model training. Video contribution additionally requires video recording and video storage.

## Rules

- Video consent does not imply public release.
- Public release consent does not imply video consent.
- Revoking consent prevents future use and blocks new submissions requiring that consent.
- Consent records include template version, language, timestamp, and salted request fingerprints.
- Raw IP addresses are not stored.

The backend enforces consent checks before contribution creation and upload sessions. Frontend controls are only a convenience layer.
