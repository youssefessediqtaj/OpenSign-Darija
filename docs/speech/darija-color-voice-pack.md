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

## Vocabulary review register

All forms below are provisional and require review by Moroccan Darija speakers,
including regional alternatives and a listening review of each recording. None is
linguistically approved here.

| Class | Proposed written form | Text and pronunciation review |
| --- | --- | --- |
| black | كحل | Pending |
| blue | زرق | Pending |
| brown | قهوي | Pending |
| green | خضر | Pending |
| orange | ليموني | Pending; potential ambiguity requires particular review |
| pink | وردي | Pending |
| red | حمر | Pending |
| white | بيض | Pending |
| yellow | صفر | Pending |

Keep a private consent and licence record with the identity of the rights holder,
allowed distribution and revocation process. Record in a quiet room without clipping
or background music; check each file for intelligibility, correct label, no clipping,
consistent loudness and trimmed silence with a Moroccan speaker before approval.
Replace files only after repeating the checks and rebuild the local web image. The
file name must remain the allowlisted semantic class, never an arbitrary path.
Local presence alone does not establish approval: asset owners are responsible for
review before installing a file. No approved recordings are supplied by this PR.

## Testing without a camera

Use the opt-in local diagnostics setup described in the main README and open
`/app/recognition?diagnostics=1` on loopback. The voice-pack tester appears before
camera activation and does not call recognition or speech services. Select a color,
then explicitly press listen. It is unavailable outside the local diagnostic gates.
A missing or undecodable clip shows an unavailable status; no TTS fallback runs.

## Future dynamic TTS evaluation (not integrated)

A future provider adapter should take explicitly approved Darija text and voice ID,
return audio bytes and format plus provenance and provider/model version, support
cancellation and explicit errors, and never fall back silently. Keep credentials on
an authorized backend, require user consent before any cloud request, and do not send
camera data. Evaluate quality with blinded Moroccan-speaker listening across regions,
latency on target devices, end-to-end privacy, published pricing and voice/model
licences before selection. Cost, latency, licensing suitability and Darija quality are
not yet measured.

- [Microsoft Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
  lists Morocco Arabic neural voices, but locale metadata does not establish colloquial
  Darija quality. It is cloud-based, incurs provider costs, and sends submitted text.
- [Piper voice inventory](https://github.com/rhasspy/piper/blob/master/VOICES.md)
  lists Arabic Jordanian rather than a verified Moroccan Darija voice. Local inference
  can keep text offline; model-specific rights, hardware cost and latency need review.

Neither option is selected or validated. Obtain speaker evaluations, current terms,
licence and pricing before any provider integration or spending.
