# Browser Console Checklist

During contribution testing, the browser console should show:

- No `404` calls to `/api/api/...`.
- No camera permission request on landmark-only synthetic contribution pages.
- No audio capture prompt.
- No failed upload session request after all required consents are granted.
- No React runtime errors when moving between consent, campaign, session, history, review, and admin pages.

Known phase 3 MVP limit: dataset contribution capture uses a synthetic landmark payload. Real MediaPipe capture remains implemented in the recognition workspace.
