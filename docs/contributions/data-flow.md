# Contribution data flow

1. The browser fetches non-personal status, catalog, and notice configuration.
2. The adult enters name, age, and city locally, selects an allowlisted sign, and
   explicitly checks the versioned consent box.
3. Camera activation is a separate click. MediaPipe evaluates face visibility,
   upper-body framing, at least one visible hand, distance, and stability locally.
   No readiness frame leaves the browser.
4. A second explicit click starts MediaRecorder. Stop creates a local object URL.
   Retake revokes that URL and discards the Blob.
5. Only “Envoyer ma contribution” creates one multipart request through Nginx to
   the API. There is no direct inference, speech, analytics, or object-storage call.
6. The API repeats all legal, age, consent-version, allowlist, size, MIME,
   signature, duration, dimensions, frame-rate, and decode checks.
7. The API generates a UUID and server UTC consent timestamp. Name/age/city enter
   the protected contributor table; the UUID object key and technical fields enter
   the video table. The private WebM enters `pending/`.
8. The public receipt returns the UUID, sign key, time, notice version, pending
   status, and rights-contact instructions—never PII or a storage locator.

No upload triggers preprocessing, training, evaluation, export, package changes,
vocabulary changes, or model activation.
