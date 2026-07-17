# Linguistic Engine

Le moteur linguistique est deterministe et controle. Il n'appelle aucun LLM externe et n'envoie aucun message a un tiers.

Etapes:

1. lire les items confirmes;
2. resoudre les concepts actifs;
3. chercher un template compatible;
4. rendre Darija arabe et latine depuis le dictionnaire;
5. rendre les aides francaises/anglaises;
6. retourner statut, avertissements, alternatives et insertions systeme.

Statuts:

- `HIGH`: template complet;
- `INCOMPLETE`: information manquante, sans invention;
- `AMBIGUOUS`: plusieurs templates possibles;
- `LOW`: aucun template fiable.

Exemples:

- `ACTION_WANT + OBJECT_WATER -> بغيت الما`
- `QUESTION_WHERE + PERSON_DOCTOR -> alternatives`
- `ACTION_WANT -> incomplete`

Le moteur n'ajoute pas automatiquement politesse, personne, lieu, douleur, urgence ou quantite sans signe, template choisi ou edition utilisateur.
