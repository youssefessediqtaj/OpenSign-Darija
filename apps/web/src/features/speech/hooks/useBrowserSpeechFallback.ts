import { useEffect, useState } from 'react';

import { browserSpeechSupported, compatibleBrowserVoices, speakWithBrowser } from '../services/browser-speech.service';

export function useBrowserSpeechFallback() {
  const [voices, setVoices] = useState(() => compatibleBrowserVoices());

  useEffect(() => {
    if (!browserSpeechSupported()) return;
    const update = () => setVoices(compatibleBrowserVoices());
    window.speechSynthesis.addEventListener('voiceschanged', update);
    update();
    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', update);
      window.speechSynthesis.cancel();
    };
  }, []);

  return {
    supported: browserSpeechSupported(),
    voices,
    speak: speakWithBrowser,
    stop: () => {
      if (browserSpeechSupported()) window.speechSynthesis.cancel();
    },
  };
}
