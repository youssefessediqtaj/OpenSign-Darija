# Docker Notes

Docker Compose exposes the public gateway on `http://localhost:8081` by default.

The core stack contains only web, API, inference, offline speech, and Nginx. It does not
start PostgreSQL, Redis, MinIO, migration/seed jobs, or dataset-import workers. The
optional `ml` profile runs a one-shot audit against files already present in the mounted
workspace and performs no remote data retrieval.
Override it with `NGINX_HOST_PORT=8080 docker compose up --build` if that port is free.

The inference service is only available on the internal Compose network and is not routed by Nginx.
