# Message Privacy

Les messages peuvent contenir des informations sensibles.

Regles:

- pas de landmarks dans les messages;
- pas de video;
- pas de token dans les exports;
- pas de texte complet dans les logs applicatifs;
- historique invite limite a une session identifiee par un ID local;
- suppression via soft delete.

Le stockage navigateur conserve seulement `opensign.guestSessionId` pour le mode invite.
