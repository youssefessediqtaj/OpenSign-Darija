# Browser Speech Fallback

The browser fallback uses `window.speechSynthesis` only when local speech generation fails and the user accepts the fallback.

Displayed warning:

```text
La voix Darija n’est pas disponible. Une voix arabe du navigateur sera utilisée.
```

Voice filtering prefers `ary-MA`, `ar-MA`, then `ar`. Availability and pronunciation vary by operating system and browser. The fallback is not presented as a Darija-native voice and is not guaranteed offline.
