# Docker

The base stack is intentionally small. It builds without local diagnostics:

```bash
docker compose build
docker compose up -d
docker compose ps
```

For local diagnostics use `make up` or:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

The local override supplies the web build flags and binds the gateway to loopback.
Open `http://localhost:8081/app/recognition?diagnostics=1` and activate the camera.
If the stack uses an existing external network, include the machine-specific recovery
override as the third Compose file; do not recreate the network or remove volumes.
The local browser token is not a production secret. Base-only Compose builds do not
contain the diagnostic controls, and later restarting with only the base file replaces
the local configuration. Rebuild the web image with the local override to restore it.

Expected services:

- `web`: React static application;
- `api`: public FastAPI gateway;
- `inference`: internal ONNX Runtime service;
- `speech`: internal local Arabic speech service;
- `nginx`: only public HTTP entry point on `NGINX_HOST_PORT`, default `8081`.

Only Nginx exposes a host port. The browser calls same-origin `/api/`; it never receives
internal inference or speech URLs.

Validate Compose shape with:

```bash
make compose-check
```

The optional `ml` Compose profile is for local audit/training utilities over already
present data. It is not part of the recognition runtime and performs no dataset
download.
