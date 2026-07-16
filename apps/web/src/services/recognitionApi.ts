import { apiRequest } from '../lib/api';
import type { RecognitionResponse } from '../types/api';

export const recognitionApi = {
  mock: () =>
    apiRequest<RecognitionResponse>('/api/v1/recognitions/mock', {
      method: 'POST',
      body: JSON.stringify({ source: 'web-demo', frames_count: 48 }),
    }),
};
