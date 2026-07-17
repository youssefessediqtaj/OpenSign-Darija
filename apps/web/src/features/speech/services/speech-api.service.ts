import { apiRequest } from '../../../lib/api';
import type { SpeechGeneration, SpeechVoice } from '../../../types/api';
import { guestHeaders } from '../../messages/services/messages-api.service';

export type SpeechRequest = {
  voice_id: string;
  speed: number;
  format: string;
  text_source: string;
  sensitive_confirmed?: boolean;
};

export const speechApi = {
  voices: () => apiRequest<{ voices: SpeechVoice[] }>('/api/v1/speech/voices'),
  status: () =>
    apiRequest<{
      mode: string;
      service_available: boolean;
      browser_fallback_enabled: boolean;
      voices_available: number;
    }>('/api/v1/speech/status'),
  create: (messageId: string, payload: SpeechRequest, idempotencyKey: string) =>
    apiRequest<SpeechGeneration>(`/api/v1/messages/${messageId}/speech`, {
      method: 'POST',
      headers: { ...guestHeaders(), 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(payload),
    }),
  get: (messageId: string, generationId: string) =>
    apiRequest<SpeechGeneration>(`/api/v1/messages/${messageId}/speech/${generationId}`, {
      headers: guestHeaders(),
    }),
  refreshUrl: (messageId: string, generationId: string) =>
    apiRequest<SpeechGeneration>(
      `/api/v1/messages/${messageId}/speech/${generationId}/refresh-url`,
      { method: 'POST', headers: guestHeaders() },
    ),
  delete: (messageId: string, generationId: string) =>
    apiRequest<{ status: string }>(`/api/v1/messages/${messageId}/speech/${generationId}`, {
      method: 'DELETE',
      headers: guestHeaders(),
    }),
};
