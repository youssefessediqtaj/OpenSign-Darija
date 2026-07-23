# Speech security and privacy

- browser input is a supported label key, not free text;
- API resolves and validates the Arabic label from the checksummed model package;
- service input length, speed, voice, and output format are validated;
- synthesis uses an argument array without a shell;
- no microphone permission or recording exists;
- no remote TTS request, account, token, DB row, object-storage object, or persistent cache
  is created;
- logs must never include WAV/base64 bodies or full request payloads.
