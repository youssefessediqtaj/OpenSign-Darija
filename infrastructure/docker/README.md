# Docker Notes

Docker Compose exposes the public gateway on `http://localhost:8081` by default.
Override it with `NGINX_HOST_PORT=8080 docker compose up --build` if that port is free.

The inference service is only available on the internal Compose network and is not routed by Nginx.
