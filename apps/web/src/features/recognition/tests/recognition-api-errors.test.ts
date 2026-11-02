import { describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../../shared/api/client';
import { landmarkRecognitionApi, recognitionErrorMessage } from '../services/recognition-api';
import type { WordLandmarkSequencePayload } from '../domain/recognition-contract';

describe('recognition API error mapping', () => {
  it('does not describe HTTP 422 as a backend outage', () => {
    const message = recognitionErrorMessage(
      new ApiError(
        'Les donnees envoyees sont invalides.',
        'VALIDATION_ERROR',
        { errors: [{ loc: ['body', 'frames', 0, 'timestamp_ms'] }] },
        422,
      ),
    );
    expect(message).toMatch(/format attendu/i);
    expect(message).not.toMatch(/backend est indisponible/i);
  });

  it('keeps network failures mapped to backend unavailable', () => {
    expect(recognitionErrorMessage(new TypeError('Failed to fetch'))).toMatch(/backend est indisponible/i);
  });

  it('maps model unavailability to the specific French message', () => {
    expect(recognitionErrorMessage(new ApiError('', 'MODEL_NOT_READY', {}, 503)))
      .toBe('Modèle de reconnaissance indisponible.');
  });

  it('maps common HTTP statuses to user-facing messages', () => {
    expect(recognitionErrorMessage(new ApiError('', '', {}, 400))).toMatch(/invalide/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 401))).toMatch(/expire/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 403))).toMatch(/autorise/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 413))).toMatch(/volumineuse/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 429))).toMatch(/tentatives/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 502))).toMatch(/service de calcul/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 504))).toMatch(/expiré/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 503))).toMatch(/temporairement indisponible/i);
  });
});

describe('recognition request cancellation', () => {
  it('propagates cancellation for color inference', async () => {
    const fetchMock = vi.fn((_url: unknown, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    }));
    vi.stubGlobal('fetch', fetchMock);
    try {
      const controller = new AbortController();
      const payload = {} as WordLandmarkSequencePayload;
      const pending = landmarkRecognitionApi.submitColorExperiment(payload, 'test-token', controller.signal);
      controller.abort();
      await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
      expect(fetchMock).toHaveBeenCalledOnce();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
