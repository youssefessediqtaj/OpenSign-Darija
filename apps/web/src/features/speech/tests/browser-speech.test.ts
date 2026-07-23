import { beforeEach, describe, expect, it, vi } from 'vitest';

import { compatibleBrowserVoices, speakWithBrowser } from '../services/browser-speech.service';

class FakeUtterance {
  lang = '';
  voice: SpeechSynthesisVoice | null = null;
  rate = 1;
  volume = 1;

  constructor(public text: string) {}
}

describe('Arabic browser speech fallback', () => {
  const speak = vi.fn();
  const cancel = vi.fn();
  const voices = [
    { name: 'Generic Arabic', lang: 'ar' },
    { name: 'Moroccan Arabic', lang: 'AR-MA' },
    { name: 'Darija', lang: 'ary-MA' },
  ] as SpeechSynthesisVoice[];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance);
    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: { getVoices: () => voices, speak, cancel },
    });
  });

  it('prioritizes ar-MA, then Darija, then generic Arabic', () => {
    expect(compatibleBrowserVoices().map((voice) => voice.lang)).toEqual([
      'AR-MA',
      'ary-MA',
      'ar',
    ]);
  });

  it('speaks once with the highest-priority Moroccan Arabic voice', () => {
    const utterance = speakWithBrowser('سلام', 1, 1) as unknown as FakeUtterance;
    expect(cancel).toHaveBeenCalledOnce();
    expect(speak).toHaveBeenCalledOnce();
    expect(utterance.text).toBe('سلام');
    expect(utterance.lang).toBe('AR-MA');
    expect(utterance.voice?.name).toBe('Moroccan Arabic');
  });
});
