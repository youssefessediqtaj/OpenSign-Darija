# Local MoSL video dataset card

## Scope

The only active data source is the already-present native copy under
`ml/data/external/mosl-video-dataset/`: 2,216 readable MP4 files and a matching local
manifest. Raw videos, landmarks, and model outputs remain local/ignored; no public
collection, contribution, upload, export, or remote-ingestion workflow is mounted.

## Audit snapshot

- 2,216 manifest/video rows, 222,795,265 bytes
- 1,941 Diverse; 71 Letters; 130 Numbers; 15 Pronouns; 59 Days/Months/Seasons
- 1,591 valid non-empty normalized labels; 15 invalid-label videos
- 2,197 unique binary checksums and valid checksum-keyed NPZ caches
- 10 ambiguous duplicate checksum groups covering 29 rows / 19 duplicate extras,
  excluded from training
- 29 normalized label keys map to multiple Arabic display strings and are excluded for
  label ambiguity; this includes the otherwise frequent `لون` and `نادي`
- label outcomes: 11 supported for training, 1,539 insufficient, 41 quality-excluded,
  and 1 invalid
- zero missing/invalid processed artifacts
- manifest SHA-256 `558241beba4b6d0b31ab2a3a22ff584a3f47274f3a57aed153dd0bf149d73d62`

## Training policy

All valid videos are included in preprocessing/audit. A class needs at least five
independent usable examples for the training-eligible report and a separate train,
validation, and test member. After collision and label-ambiguity exclusions, 11 labels/59
samples meet that threshold: eight numeric keys (`11`, `12`, `14`, `15`, `16`, `17`, `18`,
`19`) and three unambiguous lexical keys (`اب`, `احب`, `سوق`). Their deterministic split
is 37 train / 11 validation / 11 test.

The active model uses only the three lexical labels and 15 samples, split 9/3/3. Under the
declared validation-only scope rule, this `lexical_min5` scope improved validation macro F1
from 0.3333 to 1.0000 and Top-1 from 0.3636 to 1.0000 versus the mixed 11-label scope. The
active validation and test sets contain only one example per class, so these comparisons
are unstable and do not establish production quality.

Binary duplicates are grouped globally before deterministic label-stratified splitting.
No checksum crosses splits, and the known/OOV pools have no checksum overlap. Signer
identity is absent from the local manifest/filenames, so signer-independent evaluation is
impossible and no such claim is made.

## Provenance and limits

Citation/license provenance is retained in
`docs/datasets/mendeley-mosl-v1-attribution.md` and
the historical integration reports. The local copied folder itself did not contain an
independent license file, so redistribution status must be reviewed before publishing
videos or weights. Many classes are singletons; lighting/framing/signer diversity and
physical-camera transfer are not established.
