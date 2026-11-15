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
before distributing any recording. The explicit packaging process below installs approved files at:

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

Each file must contain exactly one approved spoken color label in Moroccan Darija.
The preparation tool converts to WAV PCM signed 16-bit, mono, 24 kHz and trims
leading and trailing silence using a conservative threshold. Listen to the result:
thresholds can cut soft speech or preserve noise.

The user-confirmed prototype text forms are in
`apps/web/src/features/recognition/domain/darija-colors.ts`. They are a
review checklist, **not an approved Moroccan linguistic dictionary**. Both
blue sign variants map to one audio label.

To avoid accidentally publishing unapproved recordings, WAV clips are ignored
by Git until their provenance and voice-use rights have been reviewed.
A fresh clone therefore has *no playable Darija audio*. Playback requires an explicit
approved build manifest; a named WAV alone is not enough. Clicking the preview shows
an unavailable message, never a standard-Arabic fallback.

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

The user, a native Moroccan Darija speaker, confirmed the written forms for this prototype. Regional alternatives, pronunciation of each recording and sign-to-color mapping still require review.

| Class | Proposed written form | Pronunciation review |
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


## Preparation, review and explicit packaging

`ffmpeg`, Python 3 and Node are required. Work in a private directory outside Git.
Supply files named `<color>.wav`; FFmpeg decodes and converts them. The staging and
package paths must not already exist. Source files are never overwritten.

```bash
python3 scripts/speech/prepare_voice_pack.py prepare --source /private/source --staging /private/candidates
```

`report.json` gives hashes, duration, peak, RMS, unexpected filenames and per-label
issues. Missing/corrupt files, silence, clipping and durations outside 0.15–5 seconds
are flagged. These heuristics cannot assess pronunciation, background music, loudness
consistency, consent, licensing or recording quality. Review all of those manually;
re-record if needed. The silence gate can clip soft onsets. Staging audio is **not**
approved and must not be copied to the web assets folder.

A qualified Moroccan speaker reviews each proposed expression and listens to the
exact prepared WAV. Record regional alternatives, adjective versus standalone usage,
context, and pronunciation notes; ask a Moroccan sign-language specialist to review
sign-to-class mapping separately. Obtain speaker consent and redistribution rights.
Keep personal data and signed consent in a separate access-controlled system. The
review record below uses opaque references to those private records, not names.

Create a private JSON approval file with entries for all nine labels after each is reviewed (one entry shown):

```json
{"assets":{"red":{"sha256":"<64-character candidate SHA-256>","version":"1",
"text_approved":true,"mapping_confirmed":true,"pronunciation_approved":true,
"quality_approved":true,"audio_approved":true,"rights_approved":true,"expression":"حمر",
"review_reference":"private-review-id","rights_reference":"private-rights-id"}}}
```

```bash
python3 scripts/speech/prepare_voice_pack.py package --staging /private/candidates --approvals /private/approvals.json --output /private/approved-pack
```

Packaging rechecks WAV format and quality and requires all separate approvals, both
references, and exact expression and checksum matches. It requires nine distinct approved recordings and exports them with a
sanitized manifest. Assertions in this local record are not independently verified;
the maintainer must authenticate the reviewer and rights evidence. Never mark test
tones approved except inside isolated automated tests. The candidate and approval
records remain private; the exported manifest intentionally contains no identities.

To install for a release, copy only the exported WAVs to
`apps/web/public/audio/darija/colors/` and the exported `approved-voice-pack.json` to
`apps/web/src/features/recognition/domain/approved-voice-pack.json`, then run
`npm run build` from `apps/web`. Remove stale WAVs first. The build verifies each WAV
against the manifest and fails on unlisted files, missing files or hash mismatch.
The Docker web build invokes the same check. WAVs are Git-ignored, so a release must
explicitly provision the approved pack in its build environment; a fresh clone cannot
reproduce a voice-enabled build without the separately authorized assets. Do not
publish recordings unless distribution rights cover that release. Preserve a backup
of local private assets before changing them.

The UI shows pack registration and runtime playback status separately. A registered
file can still be unavailable at runtime, and an asset checksum does not certify
linguistic accuracy. Revocation requires removing the pack entry and rebuilding.


## User recording identification (Phase 3)

The supplied private review archive contains nine WAV candidates and full-length
backups. Its HTML page exports `user_labeled_not_publication_approval` mapping JSON.
After the user explicitly selects every label, use a private new output path:

```bash
python3 scripts/speech/prepare_voice_pack.py import-mapping --review /private/review --mapping /private/confirmed_recording_color_mapping.json --output /private/mapped-candidates
```

This verifies all nine source names and color IDs exactly once, validates candidate
format and checksums against the archive report, rejects duplicate audio hashes, and
copies the candidate bytes unchanged into canonical filenames. The generated private
`mapping-report.json` records each original name, label, final filename, checksum,
and technical metrics; it explicitly marks pronunciation, audio quality and rights
as unapproved. The output is staging, not an approved pack. Review each clip against
its full-length backup for clipped speech by listening; matching samples cannot prove
that a phoneme was not trimmed. Retain the original archive and never re-encode merely
to rename clips.

Ask the speaker separately to approve the exact hash-bound pronunciation and audio
quality, and separately authorize intended distribution. Record these permissions
privately before constructing the existing approval JSON and running `package`. A
mapping selection, written-form confirmation, or technical pass is not permission to
publish voice recordings. Do not place staging audio in public web assets or Git.

## Private mapped-candidate browser preview

In the local diagnostics page, the “Aperçu privé des enregistrements” file picker
accepts all nine canonical WAV files selected by the user. The browser uses local
object URLs and does not upload files or change the approved pack. The picker validates
names and uniqueness, not hashes, identity or audio quality: run `import-mapping`
first, then select its verified private staging files. Use the native player to play,
stop and replay; changing color or leaving the page releases the current player.
This preview is shown only behind the existing loopback diagnostics gate, and is not
available to recognition or included in the approved voice provider.

Before release, the speaker must separately approve the pronunciation and quality of
each exact hash-bound clip and authorize the intended distribution. Record those
approvals privately, then run the nine-asset packaging and build-verification workflow.
Selection in the local player does not grant any approval.
