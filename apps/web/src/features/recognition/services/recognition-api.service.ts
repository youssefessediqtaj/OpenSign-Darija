import { apiRequest } from '../../../lib/api';
import type { RecognitionResponse } from '../../../types/api';
import type { CompactLandmarkSequencePayload } from '../types/sequence.types';

export const landmarkRecognitionApi = {
  submitSequence: (payload: CompactLandmarkSequencePayload) =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions', {
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
