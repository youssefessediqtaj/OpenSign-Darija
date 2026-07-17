import { useEffect, useState } from 'react';

import type { SpeechVoice } from '../../../types/api';
import { speechApi } from '../services/speech-api.service';

export function useSpeechVoices() {
  const [voices, setVoices] = useState<SpeechVoice[]>([]);
  const [available, setAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([speechApi.voices(), speechApi.status()])
      .then(([voiceResponse, statusResponse]) => {
        if (cancelled) return;
        setVoices(voiceResponse.voices);
        setAvailable(statusResponse.service_available && voiceResponse.voices.length > 0);
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Service vocal indisponible.');
          setAvailable(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { voices, available, error };
}
