import { useEffect, useState } from 'react';

import type { Message } from '../../../types/api';
import { messagesApi } from '../services/messages-api.service';

export function useMessageDraft(message: Message | null, setMessage: (message: Message) => void) {
  const [saveState, setSaveState] = useState<'SAVED' | 'SAVING' | 'ERROR'>('SAVED');
  const messageId = message?.id;
  const finalDarijaArabic = message?.final_darija_arabic;
  const finalDarijaLatin = message?.final_darija_latin;
  const finalFrench = message?.final_french;
  const finalEnglish = message?.final_english;

  useEffect(() => {
    if (!messageId) return;
    const timeout = window.setTimeout(() => {
      setSaveState('SAVING');
      messagesApi
        .update(messageId, {
          final_darija_arabic: finalDarijaArabic,
          final_darija_latin: finalDarijaLatin,
          final_french: finalFrench,
          final_english: finalEnglish,
        })
        .then((saved) => {
          setMessage(saved);
          setSaveState('SAVED');
        })
        .catch(() => setSaveState('ERROR'));
    }, 800);
    return () => window.clearTimeout(timeout);
  }, [
    messageId,
    finalDarijaArabic,
    finalDarijaLatin,
    finalFrench,
    finalEnglish,
    setMessage,
  ]);

  return saveState;
}
