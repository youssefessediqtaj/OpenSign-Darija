import { ApiError, publicApiRequest } from '../../../shared/api/client';
import type { WordLandmarkSequencePayload } from '../domain/recognition-contract';

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
  if (status === 502) return 'Le service de calcul est inaccessible ou a renvoyé une réponse invalide.';
  if (status === 504) return 'Le calcul a expiré. Réessayez.';
  if (status === 503) return 'Le moteur de reconnaissance est temporairement indisponible.';
  return 'Le backend est indisponible.';
}

export type ExperimentalColorResult = {
  model_id: string;
  model_version: string;
  experiment_id?: string | null;
  recognition_state: 'UNKNOWN_SIGN' | 'NO_HAND_DETECTED' | 'INSUFFICIENT_FRAMES' | 'MODEL_NOT_READY' | 'PREPROCESSING_ERROR' | 'INFERENCE_ERROR';
  candidate: string | null;
  raw_score: number | null;
  calibration_status: 'UNCALIBRATED';
  experimental: true;
  diagnostics?: { feature_schema_version: string; output_shape: number[] | null; failure_stage?: string | null; top_three: Array<{ label: string; raw_score: number }> } | null;
};

export const landmarkRecognitionApi = {
  submitColorExperiment: (payload: WordLandmarkSequencePayload, token: string, signal?: AbortSignal, trace = false) =>
    publicApiRequest<ExperimentalColorResult>(`/api/v1/recognitions/colors-experimental?diagnostic=true${trace ? '&trace=true' : ''}`, {
      method: 'POST', headers: { 'x-colors-dev-token': token }, body: JSON.stringify(payload), signal,
    }),
};
