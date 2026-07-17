import { useEffect, useState } from 'react';

import type { MessageList } from '../../../types/api';
import { messagesApi } from '../services/messages-api.service';

export function useMessageHistory(filter = '') {
  const [history, setHistory] = useState<MessageList | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    messagesApi
      .list(filter)
      .then((result) => {
        if (!cancelled) setHistory(result);
      })
      .catch((caught: Error) => {
        if (!cancelled) setError(caught.message);
      });
    return () => {
      cancelled = true;
    };
  }, [filter]);

  return { history, error, reload: () => messagesApi.list(filter).then(setHistory) };
}
