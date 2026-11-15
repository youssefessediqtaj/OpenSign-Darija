import { describe, expect, it } from 'vitest';
import { DARIJA_COLOR_WORDS, darijaColorAudioUrl, isDarijaColor } from '../domain/darija-colors';

describe('local Moroccan Darija color voice pack', () => {
  it('has exactly the nine semantic COLORS_V1 keys and no legacy word labels', () => {
    expect(Object.keys(DARIJA_COLOR_WORDS)).toEqual([
      'black', 'blue', 'brown', 'green', 'orange', 'pink', 'red', 'white', 'yellow',
    ]);
    for (const label of Object.keys(DARIJA_COLOR_WORDS)) expect(isDarijaColor(label)).toBe(true);
    expect(isDarijaColor('اب')).toBe(false);
    expect(isDarijaColor('احب')).toBe(false);
    expect(isDarijaColor('سوق')).toBe(false);
  });

  it('produces same-origin static WAV paths with no user-selected text', () => {
    expect(darijaColorAudioUrl('red', '/')).toBe('/audio/darija/colors/red.wav');
    expect(darijaColorAudioUrl('blue', '/opensign')).toBe('/opensign/audio/darija/colors/blue.wav');
    expect(isDarijaColor('../private')).toBe(false);
    expect(isDarijaColor('UNKNOWN_SIGN')).toBe(false);
  });
});
