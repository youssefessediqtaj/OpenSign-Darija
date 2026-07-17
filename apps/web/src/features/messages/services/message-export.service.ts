import type { Message } from '../../../types/api';

export function exportMessageJson(message: Message) {
  return JSON.stringify(
    {
      darija_arabic: message.final_darija_arabic,
      darija_latin: message.final_darija_latin,
      french: message.final_french,
      english: message.final_english,
      semantic_sequence: message.raw_semantic_sequence,
      created_at: message.created_at,
      generation_version: message.generation_version,
    },
    null,
    2,
  );
}

export function exportMessageText(message: Message) {
  return [message.final_darija_arabic, message.final_darija_latin, message.final_french, message.final_english].filter(Boolean).join('\n');
}
