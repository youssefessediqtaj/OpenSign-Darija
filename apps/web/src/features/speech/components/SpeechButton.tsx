import { Volume2 } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '../../../components/Button';
import type { Message } from '../../../types/api';
import { useBrowserSpeechFallback } from '../hooks/useBrowserSpeechFallback';
import { useSpeechGeneration } from '../hooks/useSpeechGeneration';
import { useSpeechVoices } from '../hooks/useSpeechVoices';
import { SpeechConfirmationDialog } from './SpeechConfirmationDialog';
import { SpeechFallbackNotice } from './SpeechFallbackNotice';
import { SpeechPlayer } from './SpeechPlayer';
import { SpeechSpeedControl } from './SpeechSpeedControl';
import { VoiceSelector } from './VoiceSelector';

export function SpeechButton({ message }: { message: Message }) {
  const { voices, available, error: voiceError } = useSpeechVoices();
  const defaultVoice = useMemo(() => voices.find((voice) => voice.is_default)?.id ?? voices[0]?.id ?? '', [voices]);
  const [voiceId, setVoiceId] = useState(defaultVoice);
  const [speed, setSpeed] = useState(1);
  const [volume, setVolume] = useState(1);
  const [confirming, setConfirming] = useState(false);
  const speech = useSpeechGeneration(message);
  const fallback = useBrowserSpeechFallback();
  const selectedVoice = voiceId || defaultVoice;
  const hasText = Boolean(message.final_darija_arabic || message.generated_darija_arabic);
  const sensitive = message.risk_level !== 'NORMAL';
  const disabled = !hasText || !selectedVoice || message.status !== 'COMPLETED' || speech.state === 'GENERATING';

  async function requestSpeech(confirmed = false) {
    if (sensitive && !confirmed) {
      setConfirming(true);
      return;
    }
    setConfirming(false);
    await speech.generate(selectedVoice, speed, confirmed);
  }

  function browserFallback() {
    fallback.speak(message.final_darija_arabic || message.generated_darija_arabic || '', speed, volume);
  }

  return (
    <section className="space-y-3 rounded-md border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Voix synthétique expérimentale en Darija</h2>
          <p className="text-xs text-slate-600 dark:text-slate-300">Aucune lecture automatique. Vérifiez les messages sensibles avant de parler.</p>
        </div>
        <Button disabled={disabled || !available} onClick={() => requestSpeech()}>
          <span className="inline-flex items-center gap-2"><Volume2 size={16} /> Parler</span>
        </Button>
      </div>
      {voices.length > 0 && (
        <VoiceSelector voices={voices} value={selectedVoice} onChange={setVoiceId} />
      )}
      <SpeechSpeedControl speed={speed} onChange={setSpeed} />
      {confirming && (
        <SpeechConfirmationDialog
          riskLevel={message.risk_level}
          onCancel={() => setConfirming(false)}
          onConfirm={() => requestSpeech(true)}
        />
      )}
      {(voiceError || speech.state === 'FALLBACK_AVAILABLE') && (
        <SpeechFallbackNotice onUseFallback={browserFallback} />
      )}
      {voiceError && <p className="text-xs text-red-700">{voiceError}</p>}
      {speech.error && <p className="text-xs text-red-700">{speech.error}</p>}
      {speech.state === 'GENERATING' && <p className="text-xs text-slate-600">Generation audio en cours…</p>}
      {speech.generation?.audio && (
        <SpeechPlayer generation={speech.generation} volume={volume} speed={speed} onVolume={setVolume} />
      )}
      {!fallback.voices.length && speech.state === 'FALLBACK_AVAILABLE' && (
        <p className="text-xs text-red-700">Aucune voix arabe compatible n’est disponible dans ce navigateur.</p>
      )}
    </section>
  );
}
