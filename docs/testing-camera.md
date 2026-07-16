# Testing Camera

## Without Webcam

Playwright tests mock `navigator.mediaDevices` and use a canvas stream, so CI does not need a real camera:

```bash
cd apps/web
npm run test:e2e
```

## With Webcam

Run the app locally on `localhost`, open `/app/recognition`, click `Activer la camera`, and verify:

- permission accepted and denied;
- camera selection;
- landmarks overlay;
- framing instructions;
- manual capture;
- backend result;
- camera stop on leaving the page.

## Mobile

Test Chrome Android and Safari iOS in portrait and landscape. HTTPS is required outside localhost.
