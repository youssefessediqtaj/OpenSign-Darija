# Architecture

OpenSign Darija est organise en monorepo afin de garder des contrats clairs entre interface web, API publique, inference IA et futurs modules mobiles.

## Flux

```text
Frontend web
  -> Backend API
  -> Service inference interne
```

Le service d’inference n’est pas expose par Nginx. Toute politique d’authentification, validation, journalisation et controle des donnees passe par le backend principal.

## Services

- Web: experience React mobile-first, accessible, avec routes publiques et espace `/app` protege.
- API: point d’entree public, auth JWT, donnees metier, seed, migrations et orchestration inference.
- Inference: contrat IA isole, modele simule, interfaces pretes pour extraction landmarks, preprocessing, registre de modele et ONNX.
- PostgreSQL: persistance applicative.
- Redis: cache/session/rate limiting futur.
- MinIO: stockage objet futur pour artefacts, jamais pour publication automatique de videos.
