export function browserSpeechSupported() {
  return 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

export function compatibleBrowserVoices() {
  if (!browserSpeechSupported()) return [];
  return window.speechSynthesis
    .getVoices()
    .filter((voice) => {
      const language = voice.lang.toLowerCase();
      return ['ary-ma', 'ar-ma', 'ar'].some((locale) => language.startsWith(locale));
    })
    .sort((left, right) => {
      const priority = (language: string) => {
        const normalized = language.toLowerCase();
        if (normalized.startsWith('ar-ma')) return 0;
        if (normalized.startsWith('ary-ma')) return 1;
        return 2;
      };
      return priority(left.lang) - priority(right.lang);
    })
    .map((voice) => ({ name: voice.name, lang: voice.lang, native: voice }));
}

export function speakWithBrowser(text: string, speed: number, volume: number) {
  const voices = compatibleBrowserVoices();
  if (!voices.length) {
    throw new Error('Aucune voix arabe compatible n’est disponible dans ce navigateur.');
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = voices[0].lang;
  utterance.voice = voices[0].native;
  utterance.rate = speed;
  utterance.volume = volume;
  window.speechSynthesis.speak(utterance);
  return utterance;
}
