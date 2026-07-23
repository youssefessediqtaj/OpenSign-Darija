import { publicApiRequest } from '../../../shared/api/client';

export type SignSpeechResponse = {
  generation_id: string;
  status: string;
  audio?: {
    url: string;
    mime_type: string;
    duration_ms?: number;
    expires_at?: string;
  } | null;
};

export const speechApi = {
  createForSign: (labelKey: string) =>
    publicApiRequest<SignSpeechResponse>('/api/v1/speech/sign', {
      method: 'POST',
      body: JSON.stringify({ label_key: labelKey }),
    }),
};
