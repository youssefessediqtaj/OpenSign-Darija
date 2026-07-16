import { useMutation } from '@tanstack/react-query';

import { landmarkRecognitionApi } from '../services/recognition-api.service';
import type { CompactLandmarkSequencePayload } from '../types/sequence.types';

export function useRecognitionSubmission() {
  return useMutation({
    mutationFn: (payload: CompactLandmarkSequencePayload) =>
      landmarkRecognitionApi.submitSequence(payload),
  });
}
