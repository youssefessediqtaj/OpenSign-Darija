# Offline Arabic speech adapter

- Name: `opensign-system-arabic-v1`
- Provider: local operating-system speech engine
- Preferred locale: `ar-MA`/Darija-facing label
- Fallback locale: `ar`
- Output: mono WAV at 22,050 Hz
- External model/API: none
- Voice cloning: none
- Input scope: Arabic labels resolved from the active recognition package only

macOS uses the installed `Majed` Arabic system voice; the Docker image uses local
`espeak-ng`. Both execute without a shell or network call, write only an ephemeral
temporary WAV, validate the result, and return it in memory. The output is intelligible
Arabic system TTS but is not claimed to be a native or high-quality Moroccan voice.

Known limitations include dialect pronunciation, names/diacritics, browser autoplay
policies, and lack of human listening-quality evaluation. The browser's Arabic
`speechSynthesis` voice is a last-resort playback fallback when service audio cannot be
played.
