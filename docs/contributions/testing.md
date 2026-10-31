# Contribution testing

Automated API coverage includes configuration, notice, five-sign allowlist,
adult/consent/version gates, strict multipart parsing, size/MIME/signature/duration
validation, UUID paths, SHA-256, private permissions, receipt minimization,
duplicates, rate/origin controls, storage rollback, withdrawal, deletion
anonymization, export eligibility, retention reporting, and core-health isolation.

Frontend tests cover the disabled no-PII state, exact catalog, form and consent,
underage block, explicit camera start, face/hand/stability policy, MediaRecorder
format/maximum stop, preview, retake, multipart save, track cleanup, and object-URL
revocation. Playwright covers disabled and isolated enabled record/retake/save
flows plus recognition regression and network assertions.

```bash
make test-backend
make test-frontend
make test-e2e
make test-all
make architecture-check
make compose-check
```

The isolated enabled Playwright test uses an in-browser generated camera and
route-controlled legal configuration. It does not establish legal readiness or
reference-video approval. A real Docker API upload and a physical-camera walkthrough
must be recorded separately in the final report.
