# Recognition privacy

The live camera stream and MediaPipe pixel processing stay in the browser. The core API
receives only a transient normalized landmark sequence, presence masks, boundary
metadata, and aggregate quality values. It does not persist the request or prediction.

Strict validation forbids raw video, JPEG/PNG frames, canvas exports, screenshots,
base64 camera data, arbitrary audio, microphone data, and unknown extra fields. The
browser never calls inference directly. Nginx sets `Permissions-Policy` to allow this
origin's camera and deny microphone access.

Landmarks still describe a person's body motion and should be treated as sensitive in
transport and logs even though they are not raw pixels. The runtime does not turn camera
sessions into dataset contributions and has no public contribution/import workflow.
