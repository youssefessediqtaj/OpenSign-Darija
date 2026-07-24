# Automatic isolated-sign recognition flow

The public route `/app/recognition` is anonymous and has one required action:
`Activer la caméra`. There are no manual capture, finish, recognition, or submit controls.

## Authoritative state machine

```text
CAMERA_OFF
  -> INITIALIZING
  -> WAITING_FOR_SIGN
  -> CAPTURING
  -> RECOGNIZING
  -> DISPLAYING
  -> SPEAKING (known result only)
  -> COOLDOWN
  -> WAITING_FOR_SIGN
```

`ERROR` is recoverable by stopping and activating the camera again. UNKNOWN results take
the `DISPLAYING -> COOLDOWN` path and are never sent to speech.

`RecognitionFlowState` is the sole lifecycle authority. The camera, MediaPipe loop,
segmenter, API call, speech attempt, and cooldown react to it; capture state is not split
across competing boolean flags.

## Boundary detection

Every MediaPipe frame contributes hand presence, pose visibility, wrist/elbow/hand
motion, and a normalized pose descriptor. The segmenter keeps an eight-frame rolling
pre-roll and learns a resting baseline from stable visible-hand frames.

Dynamic start requires motion energy above the configured threshold for consecutive
frames. Static start requires a stable hand configuration sufficiently different from
the learned rest pose for the dwell interval. This prevents a timer alone from defining
a sign.

While capturing, the segmenter:

- retains the pre-roll;
- ends after low motion persists for the stability interval;
- includes a three-frame post-roll;
- rejects too-short or landmark-poor captures;
- safely finalizes at the maximum duration;
- samples usable frames to exactly `60 x 75 x 3` finite coordinates.

The API receives the boundary kind, reliability decision, usable-frame count, aggregate
quality values, and normalized landmarks. It does not receive browser pixels or audio.

## UNKNOWN and duplicate handling

The API rejects unusable durations, insufficient hand coverage, missing frames, unreliable
boundaries, and invalid tensors before or alongside calibrated model confidence. The
public result is either a supported Arabic label or UNKNOWN.

After every result, the segmenter enters cooldown. A new capture is not permitted until
the cooldown has elapsed and the hands have returned close to the resting baseline (or
left the frame) for a stable reset interval. A compact sequence descriptor is compared
with the last recognized capture inside the duplicate window, suppressing the same held
pose. The same sign may be recognized again after a real reset.

## Speech

A known result is displayed and submitted once to `POST /api/v1/speech/sign` by label key.
The API resolves the package-owned Arabic text and requests offline system TTS using
`ar-MA`, then `ar` if needed. If service audio or autoplay fails, the browser Arabic voice
is attempted. Speech failure leaves the text visible and cannot fail recognition.

## Privacy and network boundary

```text
camera pixels (browser only)
  -> MediaPipe landmarks (browser only)
  -> POST /api/v1/recognitions/word
  -> API calls internal /predict/word
  -> compact recognized/unknown response
  -> API calls internal speech service for known labels
```

The browser never contacts the inference service. Strict request validation forbids extra
raw-media fields, and Nginx disables microphone permission.
