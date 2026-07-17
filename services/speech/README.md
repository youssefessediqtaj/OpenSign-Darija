# Speech Service

Service mock reserve a la future synthese vocale Darija.

Phase 5 expose uniquement:

- `GET /health`
- `POST /prepare`

`POST /prepare` retourne toujours `not_implemented`. Aucun audio n'est genere, aucun service cloud n'est appele, et le texte n'est pas envoye a un tiers.
