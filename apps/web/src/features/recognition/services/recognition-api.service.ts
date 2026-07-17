import { apiRequest } from '../../../lib/api';
import type { ActiveModel, RecognitionMode, RecognitionResponse } from '../../../types/api';
import type { CompactLandmarkSequencePayload } from '../types/sequence.types';

export const landmarkRecognitionApi = {
  modes: () => apiRequest<RecognitionMode[]>('/api/v1/recognition-modes'),
  activeModel: (taskType: 'ALPHABET_STATIC' | 'WORD_ISOLATED') =>
    apiRequest<ActiveModel>(`/api/v1/models/active?task_type=${taskType}`),
  submitSequence: (payload: CompactLandmarkSequencePayload) =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  submitWordSequence: (payload: CompactLandmarkSequencePayload) =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions/word', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  submitAlphabet: (payload: {
    sequence_id: string;
    captured_at: string;
    feature_schema_version: '1.0.0';
    hand: 'left' | 'right' | 'unknown';
    features: number[];
    presence_mask: number[];
    stability_frames: number;
    anonymous_session_id?: string;
  }) =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions/alphabet', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  confirm: (recognitionId: string, predictionId: string) =>
    apiRequest<{ status: string }>(`/api/v1/recognitions/${recognitionId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ prediction_id: predictionId }),
    }),
  correct: (recognitionId: string, correctSignId: string, reason = 'wrong_prediction') =>
    apiRequest<{ status: string }>(`/api/v1/recognitions/${recognitionId}/correct`, {
      method: 'POST',
      body: JSON.stringify({ correct_sign_id: correctSignId, reason }),
    }),
};
