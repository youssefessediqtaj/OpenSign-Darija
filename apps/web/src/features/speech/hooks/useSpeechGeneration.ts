import { useState } from 'react';

import type { Message, SpeechGeneration } from '../../../types/api';
import { speechApi } from '../services/speech-api.service';
import type { SpeechState } from '../types/speech.types';

export function useSpeechGeneration(message: Message) {
  const [generation, setGeneration] = useState<SpeechGeneration | null>(null);
  const [state, setState] = useState<SpeechState>('IDLE');
  const [error, setError] = useState<string | null>(null);

  async function generate(voiceId: string, speed: number, sensitiveConfirmed: boolean) {
    setError(null);
    setState('GENERATING');
    try {
      const response = await speechApi.create(
        message.id,
        {
          voice_id: voiceId,
          speed,
          format: 'wav',
          text_source: message.final_darija_arabic ? 'final_darija_arabic' : 'generated_darija_arabic',
          sensitive_confirmed: sensitiveConfirmed,
        },
        crypto.randomUUID(),
      );
      setGeneration(response);
      setState(response.audio ? 'READY' : 'QUEUED');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Generation vocale impossible.');
      setState('FALLBACK_AVAILABLE');
    }
  }

  return { generation, state, error, generate, setState };
}
