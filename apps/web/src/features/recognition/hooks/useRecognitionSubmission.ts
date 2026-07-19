import { useMutation } from '@tanstack/react-query';

import { landmarkRecognitionApi } from '../services/recognition-api.service';
import type { WordLandmarkSequencePayload } from '../types/sequence.types';

export function useRecognitionSubmission() {
  return useMutation({
    mutationFn: (payload: WordLandmarkSequencePayload) =>
      landmarkRecognitionApi.submitWordSequence(payload),
  });
}
