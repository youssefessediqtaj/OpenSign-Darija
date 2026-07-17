# Speech Model Card

Name: OpenSign local experimental speech provider

Version: `opensign-tone-v1`

Architecture: deterministic local waveform synthesizer used to exercise the speech architecture, audio validation, storage, playback and fallback workflows.

Dataset: none.

License: Apache-2.0 project code. No external model weights are bundled.

Language/accent: internal locale `ary-MA`; fallback `ar`. This is not a natural Moroccan human voice.

Intended use: private, user-triggered playback of finalized OpenSign Darija messages during development and early accessibility testing.

Prohibited use: voice cloning, impersonation, automatic background playback, speech-to-text, music generation, or presenting the output as a perfect Moroccan speaker.

Limitations: pronunciation is synthetic and experimental; Arabizi and unknown names may be poor; no human quality validation has been completed.

Hardware: CPU.

Update procedure: any future neural model must include license, checksum, model metadata, source repository, commercial-use status and attribution requirements before activation.
