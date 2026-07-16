# Security

Mesures phase 1:

- secrets uniquement via variables d’environnement;
- mots de passe haches avec Argon2;
- tokens JWT signes;
- validation Pydantic stricte;
- erreurs structurees;
- CORS configurable;
- SQLAlchemy pour requetes parametrees;
- Nginx avec headers de securite;
- taille de requete limitee;
- preparation Redis pour rate limiting futur;
- pas de stockage de donnees biometriques dans cette phase.

Les logs techniques ne doivent pas contenir de mot de passe, token, video ou contenu sensible.

OpenSign Darija ne remplace pas un interprete professionnel et n’est pas certifie pour des decisions medicales, juridiques, financieres ou d’urgence.
