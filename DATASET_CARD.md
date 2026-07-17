# OpenSign Darija Dataset Card

## Dataset

OpenSign Darija pilot dataset for Moroccan Sign Language contribution workflows.

## Status

Development scaffold. Not a public release.

## Contents

- Landmark sequences for approved contributions.
- Optional private video object references only when explicit video consent exists.
- No audio.
- No direct email or auth user ID in exports.
- Public external source registry for Mendeley MoSL v1 and Kaggle Moroccan LSM Alphabet.

## Consent

Consent is recorded per type and can be revoked. Landmark processing/storage, research use, and model training are required for landmark-only contribution. Video recording/storage are separate optional consents.

## Intended Use

Research, validation of collection workflows, and future model training after sufficient quality review.

External datasets are task-separated:

- `ALPHABET_STATIC`: Kaggle alphabet images, disabled until license verification and label review.
- `WORD_ISOLATED`: Mendeley MoSL v1 videos, CC BY 4.0, imported only as local immutable raw data.

ScienceDirect DOI `10.1016/j.dib.2025.112395` documents the Mendeley dataset and is not counted as a separate dataset.

## Not Intended For

- Identification of contributors.
- Public video release without explicit release process.
- Medical, legal, or emergency decision automation.

## Splits

Splits are assigned by anonymous contributor ID to avoid contributor leakage across train, validation, and test.

## Limitations

The current phase 3 frontend dataset capture path uses synthetic landmarks. Real camera MediaPipe extraction exists in the phase 2 recognition workspace and still needs integration into dataset contribution capture before real dataset collection.

No class counts, signer-independent claims, Kaggle training, alphabet model metrics, or Mendeley model metrics are asserted before local archive import and audit.
