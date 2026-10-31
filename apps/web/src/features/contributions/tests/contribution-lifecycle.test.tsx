import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { useContributionRecording } from '../hooks/useContributionRecording';

class FakeMediaRecorder {
  static isTypeSupported = () => true;
  state: RecordingState = 'inactive';
  mimeType: string;
  ondataavailable: ((event: BlobEvent) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(_: MediaStream, options?: MediaRecorderOptions) {
    this.mimeType = options?.mimeType ?? 'video/webm';
  }

  start() {
    this.state = 'recording';
  }

  stop() {
    if (this.state !== 'recording') return;
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['recorded'], { type: this.mimeType }) } as BlobEvent);
    this.onstop?.();
  }
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('MediaRecorder', FakeMediaRecorder);
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test-preview');
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it('starts on explicit invocation, auto-stops at the maximum and revokes preview URLs', () => {
  const { result, unmount } = renderHook(() => useContributionRecording(1));
  const stream = {} as MediaStream;
  expect(result.current.isRecording).toBe(false);
  act(() => {
    expect(result.current.start(stream)).toBe(true);
  });
  expect(result.current.isRecording).toBe(true);
  act(() => {
    vi.advanceTimersByTime(1000);
  });
  expect(result.current.isRecording).toBe(false);
  expect(result.current.preview?.url).toBe('blob:test-preview');
  expect(result.current.preview?.blob.type).toContain('video/webm');
  unmount();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test-preview');
});

it('retake discards and revokes the previous object URL', () => {
  const { result } = renderHook(() => useContributionRecording(10));
  act(() => {
    result.current.start({} as MediaStream);
    result.current.stop();
  });
  expect(result.current.preview).not.toBeNull();
  act(() => result.current.discard());
  expect(result.current.preview).toBeNull();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test-preview');
});

it('does not create a late preview URL when unmounted during recording', () => {
  const { result, unmount } = renderHook(() => useContributionRecording(10));
  act(() => {
    result.current.start({} as MediaStream);
  });

  unmount();

  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
