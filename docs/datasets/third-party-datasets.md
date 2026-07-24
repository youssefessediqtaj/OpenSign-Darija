# Third-Party Dataset Provenance Records

These records preserve attribution and known license metadata from an earlier
external-dataset evaluation. They are archival documentation only.

The current OpenSigne Darija core:

- does not register either source at runtime;
- exposes no external-dataset or alphabet API;
- contains no Kaggle or Mendeley downloader or archive importer;
- performs no network dataset ingestion; and
- does not use either cited source as an active training input.

## Mendeley MoSL v1

- Historical source code: `mendeley_mosl_v1`
- Title: A Dataset for Moroccan Sign Language (MoSL)
- Authors: FATIMA BEN ZAID, Mohamed BENADDY, Abdelbasset BOUKDIR
- Version: 1
- DOI: 10.17632/23phgyt3mt.1
- Recorded license for the cited release: CC BY 4.0
- Attribution record: `docs/datasets/mendeley-mosl-v1-attribution.md`
- Related article: DOI 10.1016/j.dib.2025.112395

The related ScienceDirect article documents the same Mendeley release; it must
not be counted as another dataset. The current local 2,216-video corpus was
imported from a local project tree, not through Mendeley tooling. Its equivalence
to the cited Mendeley release is UNCONFIRMED. This citation therefore preserves
the public release's attribution but does not assign its license or provenance
to the local files.

## Kaggle Moroccan LSM Alphabet

- Historical source code: `kaggle_moroccan_lsm_alphabet`
- Kaggle slug: `walidlasseg/moroccan-sign-language-lsm-alphabet-dataset`
- Historical task: `ALPHABET_STATIC`
- Recorded license status: `TO_VERIFY` / UNCONFIRMED

No Kaggle data is present in the active training workflow. The former source
registration, downloader, alphabet pipeline, runtime mode, and API surface have
been removed. This record grants no permission to download, train on, or
redistribute the dataset.

## Active Local Corpus

The active isolated-sign workflow reads the existing local corpus at
`ml/data/external/mosl-video-dataset/`. It performs local scan, audit,
preprocessing, checksum-safe splitting, training, and validation only. The local
source project had no license file, so public redistribution rights remain
UNCONFIRMED and must be established separately.
