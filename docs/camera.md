# Camera lifecycle

The browser requests camera permission only after `Activer la caméra`; it never requests
microphone permission. Default constraints prefer a front-facing `1280 x 720`, 30 FPS
stream. The preview is mirrored visually while anatomical left/right landmark blocks are
kept in model order.

Once granted, the application initializes MediaPipe and automatically enters
`WAITING_FOR_SIGN`. There is no device/settings panel in the normal one-camera case. A
small informational note appears only when multiple video inputs are detected; selection
is otherwise automatic.

`Éteindre la caméra`, route teardown, or component teardown stops every media track,
cancels animation frames/audio/timers, invalidates outstanding recognition work, resets
the segmenter, and returns to `CAMERA_OFF`. Camera APIs require HTTPS outside localhost.

Permission denial, missing hardware, insecure context, device-in-use, and detector load
errors are rendered as user-facing messages without revealing a manual capture fallback.
