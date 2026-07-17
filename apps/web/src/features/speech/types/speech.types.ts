export type SpeechState =
  | 'IDLE'
  | 'CONFIRMING'
  | 'QUEUED'
  | 'GENERATING'
  | 'READY'
  | 'PLAYING'
  | 'PAUSED'
  | 'STOPPED'
  | 'EXPIRED'
  | 'FALLBACK_AVAILABLE'
  | 'ERROR';

export type BrowserVoice = {
  name: string;
  lang: string;
};
