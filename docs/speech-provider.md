# Offline speech providers

`local-darija` and `local-arabic-fallback` use the same installed system speech engine;
their distinction makes preferred vs fallback locale explicit. macOS uses `say -v Majed`
and Docker installs `espeak-ng -v ar`. Arguments are passed directly without a shell.

No voice weights, text, or audio are sent to an external provider. Temporary WAV files
are deleted immediately after validation. The providers are experimental and must not be
described as native Moroccan voices or used for cloning/impersonation.
