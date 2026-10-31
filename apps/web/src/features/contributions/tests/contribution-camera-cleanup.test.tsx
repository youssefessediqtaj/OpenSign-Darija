import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

import { useHolisticLandmarker } from '../../recognition/hooks/useHolisticLandmarker';
import { useContributionCamera } from '../hooks/useContributionCamera';

vi.mock('../../recognition/hooks/useHolisticLandmarker', () => ({
  useHolisticLandmarker: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useHolisticLandmarker).mockReturnValue({
    status: 'ready',
    error: null,
    start: vi.fn(async () => undefined),
    stop: vi.fn(),
  });
});

it('requires explicit activation and stops every camera track on unmount', async () => {
  const stopTrack = vi.fn();
  const stream = {
    getTracks: () => [{ stop: stopTrack }],
  } as unknown as MediaStream;
  const getUserMedia = vi.fn(async () => stream);
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia },
  });
  const videoRef = { current: null };
  const { result, unmount } = renderHook(() => useContributionCamera(videoRef, true, 1000));
  expect(getUserMedia).not.toHaveBeenCalled();
  await act(async () => {
    await result.current.activate();
  });
  await waitFor(() => expect(result.current.cameraActive).toBe(true));
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  unmount();
  expect(stopTrack).toHaveBeenCalledTimes(1);
});
