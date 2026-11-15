import { describe, expect, it } from 'vitest';
import { DARIJA_COLOR_WORDS, DARIJA_VOCABULARY, isDarijaColor } from '../domain/darija-colors';
import { LocalDarijaVoiceProvider } from '../domain/darija-voice-provider';

describe('local Moroccan Darija color voice pack', () => {
  it('has nine provisional classes and rejects legacy or unsafe labels', () => {
    expect(Object.keys(DARIJA_COLOR_WORDS)).toEqual(['black', 'blue', 'brown', 'green', 'orange', 'pink', 'red', 'white', 'yellow']);
    for (const label of Object.keys(DARIJA_COLOR_WORDS)) {
      expect(isDarijaColor(label)).toBe(true);
      if (isDarijaColor(label)) expect(DARIJA_VOCABULARY[label].reviewStatus).toBe('approved');
    }
    for (const label of ['اب', '../private', 'UNKNOWN_SIGN']) expect(isDarijaColor(label)).toBe(false);
  });
  it('resolves each approved semantic color to its own WAV', () => {
    for (const label of Object.keys(DARIJA_COLOR_WORDS)) {
      if (!isDarijaColor(label)) throw new Error('unexpected color');
      const provider = new LocalDarijaVoiceProvider({ assets: {
        [label]: { approved: true, sha256: 'a'.repeat(64), version: 'test', expression: DARIJA_COLOR_WORDS[label] },
      } });
      expect(provider.resolve(label)?.url).toBe(`/audio/darija/colors/${label}.wav`);
    }
  });
  it('requires a reviewed pack entry and constructs a fixed local path', () => {
    const missing = new LocalDarijaVoiceProvider();
    expect(missing.resolve('red')).toBeNull();
    const valid = new LocalDarijaVoiceProvider({ assets: { red: { approved: true, sha256: 'a'.repeat(64), version: '1', expression: 'حمر' } } });
    expect(valid.resolve('red')).toMatchObject({ url: '/audio/darija/colors/red.wav', version: '1' });
    expect(valid.resolve('../private')).toBeNull();
    expect(new LocalDarijaVoiceProvider({ assets: { red: { approved: true, sha256: 'a'.repeat(64), version: '1', expression: 'wrong' } } }).resolve('red')).toBeNull();
    expect(valid.resolve('blue')).toBeNull();
    expect(new LocalDarijaVoiceProvider({ assets: { red: { approved: false, sha256: 'a'.repeat(64), version: '1', expression: 'حمر' } } }).resolve('red')).toBeNull();
  });
});
