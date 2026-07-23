# Historical Dataset Card - Mendeley MoSL v1

## Current Status

`HISTORICAL_INACTIVE`.

This card preserves attribution and license metadata for a public MoSL release
that was evaluated earlier. The current runtime has no Mendeley registration or
external-dataset API, the repository has no Mendeley downloader or archive
importer, and this cited release is not declared as an active training input.

## Recorded Source

- Provider: Mendeley Data
- Title: A Dataset for Moroccan Sign Language (MoSL)
- Authors: FATIMA BEN ZAID, Mohamed BENADDY, Abdelbasset BOUKDIR
- Version: 1
- DOI: 10.17632/23phgyt3mt.1
- Related article: DOI 10.1016/j.dib.2025.112395
- Historical task: `WORD_ISOLATED`
- Modality: MP4 videos

The related article documents the Mendeley release and is not a separate dataset
source.

## License Provenance

The cited Mendeley release is recorded as CC BY 4.0. That license record applies
to the referenced public release; it must not be silently transferred to files
whose identity with that release has not been established.

## Relationship to the Active Local Corpus

The current workflow uses 2,216 videos imported from a local project tree into
`ml/data/external/mosl-video-dataset/`. No Mendeley download or import tooling was
used for that active path, and equivalence between the local files and the cited
Mendeley release is UNCONFIRMED. The local source project contained no license
file, so redistribution rights for the local corpus remain UNCONFIRMED.

## Known Limits

- No signer identity is available for the active local files; signer-independent
  claims are not supported.
- This card makes no accuracy, class-count, or quality claim about the cited
  Mendeley release.
- No public video serving or automatic republication is enabled.
- Any future Mendeley reuse requires an explicit import decision, checksum and
  label audit, privacy review, and confirmation that the referenced license
  applies to the exact files used.
