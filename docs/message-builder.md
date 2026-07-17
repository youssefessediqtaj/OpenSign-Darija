# Message Builder

Phase 5 ajoute un constructeur de messages Darija controle.

Flux:

```text
Reconnaissance -> confirmation/correction -> item confirme -> sequence semantique -> generation Darija -> edition finale
```

Seuls les signes confirmes ou corriges peuvent etre ajoutes depuis la reconnaissance. Les mots manuels sont marques `MANUAL_INPUT` et ne sont jamais presentes comme signes reconnus.

Routes frontend:

- `/app/messages`
- `/app/messages/new`
- `/app/messages/:messageId`
- `/app/messages/:messageId/edit`
- `/app/messages/history`
- `/app/messages/favorites`

Limites: vocabulaire pilote, templates de demonstration, pas de grammaire complete LSM marocaine.
