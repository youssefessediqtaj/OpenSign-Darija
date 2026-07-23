# Runtime Flow

The product contract is one automatic, anonymous isolated-sign loop:

```mermaid
flowchart LR
  A[Activate camera] --> B[Browser MediaPipe]
  B --> C[Automatic sign start/end]
  C --> D[60 x 75 x 3 landmarks]
  D --> E[Public API]
  E --> F[Internal ONNX inference]
  F --> G{Known?}
  G -->|yes| H[Display Arabic/Darija]
  H --> I[API calls internal speech]
  I --> J[Cooldown]
  G -->|UNKNOWN| K[Display UNKNOWN without speech]
  K --> J
  J --> C
```

Only normalized finite landmarks and approved segmentation metadata leave the
browser. The browser calls same-origin `/api` routes only. Nginx is the only public
gateway; API, inference, speech, and web containers stay internal behind it.
