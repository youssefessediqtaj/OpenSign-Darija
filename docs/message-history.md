# Message History

Les messages connectes sont associes a `user_id`. Les messages invites sont associes a `anonymous_session_id`.

Fonctions:

- brouillons;
- finalisation;
- favoris;
- duplication;
- archivage;
- suppression soft delete;
- recherche/pagination backend.

Les revisions gardent des snapshots limites et ne doivent pas contenir landmarks, video, audio ou secrets.
