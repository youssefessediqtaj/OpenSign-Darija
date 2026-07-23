import { useEffect } from 'react';

export function CameraPreview({
  stream,
  videoRef,
  isMirrored,
  children,
}: {
  stream: MediaStream | null;
  videoRef: React.RefObject<HTMLVideoElement>;
  isMirrored: boolean;
  children: React.ReactNode;
}) {
  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream, videoRef]);

  return (
    <div className="relative aspect-video overflow-hidden rounded-md bg-slate-950">
      {stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`h-full w-full object-cover ${isMirrored ? '-scale-x-100' : ''}`}
          aria-label="Aperçu caméra en direct"
        />
      ) : (
        <div className="flex h-full items-center justify-center px-6 text-center text-slate-200">
          La caméra n’est pas active.
        </div>
      )}
      {children}
      {stream && (
        <span className="absolute left-3 top-3 rounded-md bg-black/70 px-3 py-1 text-xs font-semibold text-white">
          Caméra active
        </span>
      )}
    </div>
  );
}
