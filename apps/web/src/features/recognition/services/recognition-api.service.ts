import { ApiError, apiRequest } from '../../../lib/api';
import type { ActiveModel, RecognitionMode, RecognitionResponse } from '../../../types/api';
import type { CompactLandmarkSequencePayload, WordLandmarkSequencePayload } from '../types/sequence.types';

function firstValidationField(error: ApiError): string | null {
  const errors = error.details.errors;
  if (!Array.isArray(errors)) return null;
  const first = errors[0];
  if (!first || typeof first !== 'object' || !('loc' in first) || !Array.isArray(first.loc)) return null;
  return first.loc.filter((part: unknown) => part !== 'body').join('.');
}

export function recognitionErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Le backend est indisponible.';
  const status = error.status ?? Number(error.details.status);
  if (status === 400) return 'Requete de reconnaissance invalide.';
  if (status === 401) return 'Votre session a expire.';
  if (status === 403) return 'Vous n’etes pas autorise a effectuer cette action.';
  if (status === 413) return 'La sequence capturee est trop volumineuse.';
  if (status === 422) {
    const field = import.meta.env.DEV ? firstValidationField(error) : null;
    return field
      ? `La sequence capturee ne respecte pas le format attendu. Champ invalide: ${field}.`
      : 'La sequence capturee ne respecte pas le format attendu.';
  }
  if (status === 429) return 'Trop de tentatives. Reessayez dans quelques instants.';
  if (status === 503) return 'Le moteur de reconnaissance est temporairement indisponible.';
  return 'Le backend est indisponible.';
}

export const landmarkRecognitionApi = {
  modes: () => apiRequest<RecognitionMode[]>('/api/v1/recognition-modes'),
  activeModel: (taskType: 'ALPHABET_STATIC' | 'WORD_ISOLATED') =>
    apiRequest<ActiveModel>(`/api/v1/models/active?task_type=${taskType}`),
  submitSequence: (payload: CompactLandmarkSequencePayload) =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  submitWordSequence: (payload: WordLandmarkSequencePayload) =>
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
