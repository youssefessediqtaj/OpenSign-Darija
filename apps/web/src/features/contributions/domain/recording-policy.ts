export const PREFERRED_RECORDING_MIME_TYPES = [
  'video/webm;codecs=vp9',
  'video/webm;codecs=vp8',
  'video/webm',
] as const;

export function selectRecordingMimeType(): string | null {
  if (typeof MediaRecorder === 'undefined') return null;
  return (
    PREFERRED_RECORDING_MIME_TYPES.find((mimeType) => MediaRecorder.isTypeSupported(mimeType)) ??
    null
  );
}
