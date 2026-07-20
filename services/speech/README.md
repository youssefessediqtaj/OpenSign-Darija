# Speech Service

Service local de synthèse vocale arabe pour les libellés Darija reconnus. Le runtime utilise
le moteur vocal installé dans le conteneur et n'appelle aucun service cloud.

Routes actives :

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /voices`
- `POST /synthesize`

`POST /synthesize` normalise le texte, sélectionne la voix `ar-MA` demandée (avec voix `ar`
de secours), puis retourne un fichier WAV encodé en Base64 avec ses métadonnées.
