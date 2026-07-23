import { env } from '../config/env';

type ApiErrorPayload = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status?: number;

  constructor(
    message: string,
    code = 'API_ERROR',
    details: Record<string, unknown> = {},
    status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return new ApiError(payload.error.message, payload.error.code, payload.error.details, response.status);
  } catch {
    return new ApiError('Une erreur technique est survenue.', 'HTTP_ERROR', { status: response.status }, response.status);
  }
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15_000);
  const abortFromCaller = () => controller.abort();
  init.signal?.addEventListener('abort', abortFromCaller, { once: true });
  if (init.signal?.aborted) controller.abort();
  try {
    const response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...init.headers,
      },
    });
    if (!response.ok) {
      throw await parseError(response);
    }
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timeout);
    init.signal?.removeEventListener('abort', abortFromCaller);
  }
}

export async function publicApiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  return request<T>(path, init);
}
