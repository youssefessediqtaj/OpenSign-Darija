# Message Backend Log Checklist

Lire:

```bash
docker compose logs api
docker compose logs speech
docker compose logs nginx
```

Chercher:

- exceptions SQL;
- erreurs Unicode/RTL;
- 500 sur `/api/v1/messages`;
- doublons d'items;
- contenu sensible dans les logs;
- erreurs speech mock.
