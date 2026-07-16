import { describe, expect, it, vi } from 'vitest';

import { cameraErrorMessage, mapCameraError } from '../utils/camera-errors';

describe('camera errors', () => {
  it('maps permission denied errors', () => {
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: vi.fn() } });
    expect(mapCameraError(new DOMException('denied', 'NotAllowedError'))).toBe('PERMISSION_DENIED');
    expect(cameraErrorMessage('PERMISSION_DENIED')).toMatch(/refuse/i);
  });

  it('maps missing devices', () => {
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: vi.fn() } });
    expect(mapCameraError(new DOMException('missing', 'NotFoundError'))).toBe('NOT_FOUND');
  });
});
