# Fingerspelling

Fingerspelling builds a word letter by letter. A confirmed word becomes a `FINGERSPELLED_WORD` message item and is not treated as a recognized sign.

Repeated letters require a new confirmation or neutral transition; a stable frame stream alone must not append repeated letters.
