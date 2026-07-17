import { useState } from 'react';

import type { GenerationResponse, Message } from '../../../types/api';
import { messagesApi } from '../services/messages-api.service';

export function useMessageGeneration(message: Message | null, setMessage: (message: Message) => void) {
  const [generation, setGeneration] = useState<GenerationResponse | null>(null);
  const [generating, setGenerating] = useState(false);

  async function generate() {
    if (!message || generating) return;
    setGenerating(true);
    try {
      const result = await messagesApi.generate(message.id);
      setGeneration(result);
      setMessage({
        ...message,
        status: 'READY',
        raw_semantic_sequence: result.semantic_sequence,
        generated_darija_arabic: result.result.darija_arabic ?? '',
        generated_darija_latin: result.result.darija_latin ?? '',
        generated_french: result.result.french ?? '',
        generated_english: result.result.english ?? '',
        final_darija_arabic: message.final_darija_arabic || result.result.darija_arabic || '',
        final_darija_latin: message.final_darija_latin || result.result.darija_latin || '',
        final_french: message.final_french || result.result.french || '',
        final_english: message.final_english || result.result.english || '',
        generation_strategy: result.strategy,
        generation_version: result.generation_version,
        generation_metadata: {
          ...message.generation_metadata,
          template: result.template,
          linguistic_status: result.linguistic_status,
          system_insertions: result.system_insertions,
          warnings: result.warnings,
          alternatives: result.alternatives,
        },
      });
    } finally {
      setGenerating(false);
    }
  }

  return { generation, generating, generate };
}
