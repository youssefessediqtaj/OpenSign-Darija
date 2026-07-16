import { apiRequest } from '../lib/api';
import type { VersionResponse } from '../types/api';

export const systemApi = {
  version: () => apiRequest<VersionResponse>('/api/v1/version'),
};
