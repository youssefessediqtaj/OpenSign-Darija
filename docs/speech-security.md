# Speech Security

Before generation, the API checks:

- message exists and is not deleted
- current user or guest session owns the message
- message is finalized
- final text exists and respects configured limits
- voice is active
- speed and format are allowed
- sensitive messages require explicit confirmation

Logs must not contain full message text, audio bytes, signed URLs, tokens, emails or session IDs. The service does not clone voices and does not record the microphone.
