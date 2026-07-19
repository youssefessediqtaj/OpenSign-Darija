import { describe, expect, it } from 'vitest';

import { ApiError } from '../../../lib/api';
import { recognitionErrorMessage } from '../services/recognition-api.service';

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

  it('maps common HTTP statuses to user-facing messages', () => {
    expect(recognitionErrorMessage(new ApiError('', '', {}, 400))).toMatch(/invalide/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 401))).toMatch(/expire/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 403))).toMatch(/autorise/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 413))).toMatch(/volumineuse/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 429))).toMatch(/tentatives/i);
    expect(recognitionErrorMessage(new ApiError('', '', {}, 503))).toMatch(/temporairement indisponible/i);
  });
});
