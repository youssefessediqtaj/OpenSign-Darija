export function browserSpeechSupported() {
  return 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

export function compatibleBrowserVoices() {
  if (!browserSpeechSupported()) return [];
  return window.speechSynthesis
    .getVoices()
    .filter((voice) => ['ary-MA', 'ar-MA', 'ar'].some((locale) => voice.lang.startsWith(locale)))
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
