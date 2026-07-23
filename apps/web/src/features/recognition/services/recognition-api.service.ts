import { ApiError, publicApiRequest } from '../../../lib/api';
import type { PublicRecognitionResult } from '../types/recognition-flow.types';
import type { WordLandmarkSequencePayload } from '../types/sequence.types';

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
  submitWordSequence: (payload: WordLandmarkSequencePayload) =>
    publicApiRequest<PublicRecognitionResult>('/api/v1/recognitions/word', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
