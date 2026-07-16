# Camera

The camera is requested only after the user clicks `Activer la camera`.

## Permission

The UI explains that video is processed locally, no video is recorded, and only motion landmarks are sent to the backend. The microphone is never requested.

## Constraints

Default constraints request a user-facing camera with ideal 1280x720 at up to 30 FPS. Low-power modes reduce resolution and analysis frequency.

## Selection And Stop

After permission, `enumerateDevices()` lists available cameras. The selected device id is stored as a local preference. When the user leaves the page, stops the camera, changes session, or the tab is hidden, all video tracks are stopped with `track.stop()`.

## HTTPS

Browser camera APIs require HTTPS outside `localhost`.

## Errors

The UI maps browser errors to French user messages for denied permission, missing device, insecure context, camera in use, unsupported constraints, interruptions, and system failures.
