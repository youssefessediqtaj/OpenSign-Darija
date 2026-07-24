# MoSL Video Dataset

Date: 2026-07-19

## Native Location

```text
ml/data/external/mosl-video-dataset/
├── raw/
├── manifests/
├── processed/
├── reports/
├── splits/
└── quarantine/
```

Raw videos, processed landmarks and large payloads remain out of Git.

## Source Provenance

Original local source path:

```text
Multimodal-Moroccan-Sign-Language-Generation/vedios-dataset/
```

The source folder spelling is preserved in manifests for provenance. No local source-code license file was found in the nested project; source code was therefore reimplemented natively instead of copied. Dataset licensing should continue to be checked against upstream metadata before any public redistribution.

## Import And Verification

The import target now requires an explicit local source path:

```bash
MOSL_SOURCE_DATASET_ROOT=/path/to/source/videos make ml-dataset-import
MOSL_SOURCE_DATASET_ROOT=/path/to/source/videos make ml-verify-mosl-migration
```

Current verified result:

- Source videos: 2,216
- Native videos: 2,216
- Matching checksums: 2,216
- Missing files: 0
- Unexpected files: 0
- Checksum mismatches: 0
- Video bytes: 222,795,265
- Invalid label records: 15
- Duplicate checksum extras: 19

## Category Counts

| Category | Mode | Videos |
| --- | ---: | ---: |
| Diverse | `WORD_ISOLATED` | 1,941 |
| Letters | `ALPHABET_STATIC` | 71 |
| Numbers | `WORD_ISOLATED` | 130 |
| Pronouns | `WORD_ISOLATED` | 15 |
| Days/Months/Seasons | `WORD_ISOLATED` | 59 |

Mode totals:

- `WORD_ISOLATED`: 2,145
- `ALPHABET_STATIC`: 71

## Splits And Limits

Signer identity is not available from the local filenames, so current splits are checksum-safe and class-aware but not signer-independent. Singleton classes remain excluded from trainable splits.
