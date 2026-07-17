import { useEffect, useState } from 'react';

import type { Message } from '../../../types/api';
import { messagesApi } from '../services/messages-api.service';

export function useCurrentMessage(messageId?: string) {
  const [message, setMessage] = useState<Message | null>(null);
  const [loading, setLoading] = useState(Boolean(messageId));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!messageId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    messagesApi
      .get(messageId)
      .then((loaded) => {
        if (!cancelled) setMessage(loaded);
      })
      .catch((caught: Error) => {
        if (!cancelled) setError(caught.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [messageId]);

  return { message, setMessage, loading, error };
}
