# Recognition State Machine

The browser owns recognition state because it owns camera permission, MediaPipe,
frame cadence, and duplicate suppression.

```mermaid
stateDiagram-v2
  [*] --> idle
  idle --> requesting_camera
  requesting_camera --> detecting: stream + MediaPipe ready
  requesting_camera --> camera_error
  detecting --> capturing: sign start
  capturing --> submitting: sign end + valid sequence
  submitting --> known_result: API known response
  submitting --> unknown_result: API UNKNOWN response
  known_result --> speaking
  speaking --> cooldown
  unknown_result --> cooldown
  cooldown --> detecting
```

UNKNOWN is a terminal decision for that capture and must not trigger speech. A
held sign is suppressed through cooldown and reset rules so it is not recognized
repeatedly.
