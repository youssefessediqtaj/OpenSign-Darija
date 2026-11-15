# Moroccan Darija color speech — manual local preview

This is an **opt-in, offline voice-pack playback** for the nine COLORS_V1
diagnostic candidates. It intentionally does not call the existing generic Arabic
speech service, browser `speechSynthesis`, or a cloud TTS provider.

The COLORS_V1 GRU is unvalidated and uncalibrated. **Do not automatically speak
a predicted color.** This preview only plays after the user's explicit click,
with the experimental warning still visible. Playback is not a confirmation
that the gesture was recognized correctly.

## Required audio files

Record the nine labels with a consenting native Moroccan Darija speaker.
Review pronunciation (including regional variants), rights and permitted use
before distributing any recording. Place the approved files locally at:

```
apps/web/public/audio/darija/colors/
  black.wav
  blue.wav
  brown.wav
  green.wav
  orange.wav
  pink.wav
  red.wav
  white.wav
  yellow.wav
```

Each file should contain exactly one approved spoken color label in Moroccan
Darija, not a Modern Standard Arabic substitute. Suggested recording specs:
WAV PCM signed 16-bit, mono, 24 kHz, short silence-trimmed clips. For example:

```bash
ffmpeg -i original-recording.wav -ac 1 -ar 24000 -c:a pcm_s16le red.wav
```

The provisional text forms are in
`apps/web/src/features/recognition/domain/darija-colors.ts`. They are a
review checklist, **not an approved Moroccan linguistic dictionary**. Both
blue sign variants map to one audio label.

To avoid accidentally publishing unapproved recordings, WAV clips are ignored
by Git until their provenance and voice-use rights have been reviewed.
A fresh clone therefore has *no playable Darija audio*. Clicking the preview
shows an explicit unavailable message, never a standard-Arabic fallback.

## QA checklist

- A click triggers the local WAV, with no browser speech or remote API call.
- All nine labels have a reviewed recording and correct file name.
- Test speakers from different Moroccan regions for intelligibility.
- Verify real devices (Chrome, Firefox, Safari/mobile), autoplay policy,
  volume, repeated clicks, camera stop and Sign Again cancellation.
- Reject unsupported labels and absent/malformed files without speaking.
- After independent recognition accuracy, UNKNOWN and false-acceptance checks,
  consider a separate opt-in automatic speech mode. That change requires
  explicit acceptance, accessibility review and device testing.

For future dynamic sentence generation, a Moroccan TTS model or ar-MA cloud
voice may be evaluated separately; locale names alone do not demonstrate
Darija pronunciation quality, and no Arabic default should be silently used.
