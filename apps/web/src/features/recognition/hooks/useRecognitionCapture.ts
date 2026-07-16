import { useCallback, useEffect, useState } from 'react';

export function useRecognitionCapture(onCountdownComplete: () => void) {
  const [countdown, setCountdown] = useState<number | 'start' | null>(null);

  const beginCountdown = useCallback(() => {
    setCountdown(3);
  }, []);

  const cancelCountdown = useCallback(() => setCountdown(null), []);

  useEffect(() => {
    if (countdown === null) return undefined;
    if (countdown === 'start') {
      const timeout = window.setTimeout(() => {
        setCountdown(null);
        onCountdownComplete();
      }, 500);
      return () => window.clearTimeout(timeout);
    }
    const timeout = window.setTimeout(() => {
      setCountdown(countdown > 1 ? countdown - 1 : 'start');
    }, 1000);
    return () => window.clearTimeout(timeout);
  }, [countdown, onCountdownComplete]);

  return { countdown, beginCountdown, cancelCountdown };
}
