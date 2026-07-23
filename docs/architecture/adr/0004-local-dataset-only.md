# ADR 0004: Local Dataset Only

## Status

Accepted.

## Decision

The current repository uses only the local MoSL dataset under
`ml/data/external/mosl-video-dataset/`.

## Consequences

No Kaggle, Mendeley, or ScienceDirect downloader is active in runtime or CI. The
local dataset and generated manifests remain protected; the active model is not
retrained during architecture cleanup.
