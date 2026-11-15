# Darija TTS research — Phase 2

No provider has been evaluated by Moroccan listeners or selected. Model-card claims,
locale labels and licences are not proof of naturalness, rights to all training
recordings, or suitability for accessibility use. Arabic script, code-switching,
pronunciation, naturalness, latency, memory and cost require measurement.

| Candidate | Evidence and deployment | Assessment and open questions |
| --- | --- | --- |
| Recorded approved clips | Local WAV, no inference or network | Recommended for the nine-color MVP after consent and listening review. Low runtime latency; recording and review costs remain. Cannot generate sentences. |
| [NeuTTS Air Darija](https://huggingface.co/Tilas/neutts-air-darija-v1) | Model card describes Darija adaptation, Apache-2.0 and Arabic text phonemized through eSpeak `ar`; card describes YouTube-derived training data. | Candidate for an isolated local evaluation, not a fallback. Verify training-data rights, voice consent, dependencies and licences independently. CPU/GPU, memory, latency, code-switching and Darija phonemization quality are unmeasured. |
| [HADRA / Habibi TTS Darija](https://huggingface.co/Jip7e/habibi-tts-doda-darija) | Model card describes a Darija-fine-tuned F5-TTS model and declares Apache-2.0. | A second research candidate; verify upstream code/weights and data/voice rights. Compute, memory, latency, Arabic-script and code-switching performance are unmeasured. |
| [Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support) | Cloud lists `ar-MA` Mouna and Jamal neural voices. | Locale is not evidence of colloquial pronunciation. Text leaves the device; usage is billed and terms/pricing, network latency, code-switching and licensing must be checked for the actual deployment. |
| [Coqui XTTS-v2](https://github.com/coqui-ai/TTS/blob/dev/docs/source/models/xtts.md) | Multilingual model lists Arabic, not specific Darija; model documentation identifies a separate Coqui model licence. | Local deployment may protect text but generic Arabic support does not establish Darija. Hardware, latency, cloning consent and commercial terms need review. |

For sentence-generation research, first compare the two specifically Darija-adapted
models locally on a consented, fixed evaluation set. This is a research priority,
not a claim that either is best. Test Arabic spelling variation, regional variants,
code-switching and out-of-vocabulary words with blinded Moroccan listeners; measure
CPU/GPU/RAM, latency, reliability and operational costs on target hardware. Confirm
model, dependency, training-data and speaker rights before use. Compare a cloud option
only with explicit consent, provider terms, data handling and a current price quote.
Never send camera frames or audio to a speech provider. Keep all unreviewed models out
of the release and do not synthesize production speech automatically.
