import { env } from '../config/env';
import type { ApiErrorPayload } from '../types/api';

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(message: string, code = 'API_ERROR', details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return new ApiError(payload.error.message, payload.error.code, payload.error.details);
  } catch {
    return new ApiError('Une erreur technique est survenue.', 'HTTP_ERROR', { status: response.status });
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as T;
}
