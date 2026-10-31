# Contribution security review

Implemented controls:

- fail-closed controller/CNDP/reference-video configuration;
- exact five-key server allowlist and strict multipart field set;
- adult and explicit versioned-consent enforcement;
- request/file limits, per-process IP rate limiting, restricted CORS and origin check;
- generated UUID filenames and path traversal rejection;
- MIME plus EBML signature, FFprobe metadata, and full bounded FFmpeg decode;
- private `0700` directories and `0600` files outside the web root;
- separate contributor/video tables and server UTC consent timestamp;
- SQLite transaction plus atomic promotion and compensating orphan cleanup;
- private S3 adapter with server-side encryption option and no public ACL/URL;
- structured events containing event type and UUID, never name/city/video;
- no Nginx location or receipt field that exposes raw video;
- guarded local review, deletion, retention, and staging export;
- no direct ML, inference, speech, analytics, or storage call from the browser.

Residual/operational items:

- multi-replica public deployment needs a trusted gateway/distributed rate limit;
- database encryption/backup/access and S3 public-access-block evidence need review;
- identity verification and deletion audit minimization remain controller decisions;
- approved reference media, CNDP evidence, processor contracts, transfers, and
  physical-camera testing remain blockers.
