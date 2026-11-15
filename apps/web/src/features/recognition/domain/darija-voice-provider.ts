import pack from './approved-voice-pack.json';
import { DARIJA_COLOR_WORDS, isDarijaColor, type DarijaColor } from './darija-colors';

export type ApprovedAudioAsset = { url: string; format: 'audio/wav'; version: string; sha256: string };
export interface SpeechProvider {
  resolve(color: string): ApprovedAudioAsset | null;
}

/** The build-time pack is generated only by the explicit approval pipeline. */
type VoicePack = { assets: Partial<Record<DarijaColor, { sha256: string; version: string; approved: boolean; expression: string }>> };

export class LocalDarijaVoiceProvider implements SpeechProvider {
  constructor(private readonly voicePack: VoicePack = pack) {}
  resolve(color: string): ApprovedAudioAsset | null {
    if (!isDarijaColor(color)) return null;
    const entry = this.voicePack.assets[color];
    if (!entry || entry.approved !== true || entry.expression !== DARIJA_COLOR_WORDS[color] || !/^[a-f0-9]{64}$/.test(entry.sha256) || !entry.version) return null;
    const base = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;
    return { url: `${base}audio/darija/colors/${color}.wav`, format: 'audio/wav', version: entry.version, sha256: entry.sha256 };
  }
}

// A future neural adapter must implement SpeechProvider and be explicitly selected;
// no dynamic generation or fallback is registered today.
export const speechProviderRegistry: Readonly<Record<'local', SpeechProvider>> = {
  local: new LocalDarijaVoiceProvider(),
};
