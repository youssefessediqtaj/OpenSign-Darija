# Camera and automatic-flow testing

## Automated gate

The Playwright recognition suite opens `/app/recognition`, clicks only `Activer la
caméra`, and waits. It must never click or find manual start, finish, recognize, send, or
mode-selection controls.

Deterministic frames cover rest, movement, stable ending, reset, a second gesture, and
UNKNOWN. Tests verify automatic API submission, exact `60 x 75 x 3` finite payloads,
known-result speech once, UNKNOWN without speech, cooldown/reset, no duplicate held-pose
submission, anonymous access, and absence of raw-media or direct-inference requests.

A separate case targets `http://127.0.0.1:8081` without intercepting recognition or
speech. It is skipped with an explicit reason only when the Docker health endpoint is
unavailable. Synthetic landmarks are useful for flow determinism but are not claimed to
be two known physical production signs.

## Required physical-camera gate

With the real Docker stack healthy:

1. Open `http://localhost:8081/app/recognition` in a browser with camera permission.
2. Click only `Activer la caméra`.
3. Wait for `Prêt — faites un signe`.
4. Perform one sign listed in the active package's `supported-signs.json`, end naturally,
   and verify recognition starts without another action.
5. Verify a known result is displayed and spoken once, or record the actual safe UNKNOWN
   outcome without relabeling it as success.
6. Return fully to rest, perform a second supported sign, and verify a second automatic
   cycle rather than a duplicate held-pose cycle.
7. Inspect console and network for errors, authentication redirects, raw video/image/audio
   bodies, direct inference calls, or external dataset traffic.

Physical performance and sign correctness require a person, actual camera, and knowledge
of the supported signs. Automated fake-camera evidence does not substitute for this
manual gate, and an unavailable device or unperformed sign must be reported as
`UNCONFIRMED`.
