# Docker

The normal runtime stack is intentionally small:

```bash
docker compose build
docker compose up -d
docker compose ps
```

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
