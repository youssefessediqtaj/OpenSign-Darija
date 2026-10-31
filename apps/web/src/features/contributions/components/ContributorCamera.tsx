import { useEffect } from 'react';

export function ContributorCamera({
  stream,
  videoRef,
}: {
  stream: MediaStream | null;
  videoRef: React.RefObject<HTMLVideoElement>;
}) {
  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream, videoRef]);
  return (
    <div className="relative aspect-video overflow-hidden rounded-xl bg-slate-950">
      {stream ? (
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="h-full w-full -scale-x-100 object-cover"
          aria-label="Caméra du contributeur"
        />
      ) : (
        <div className="flex h-full items-center justify-center px-6 text-center text-slate-200">
          La caméra ne démarre jamais automatiquement.
        </div>
      )}
      {stream && (
        <span className="absolute left-3 top-3 rounded-md bg-black/75 px-3 py-1 text-xs font-semibold text-white">
          Caméra active — aucune image envoyée
        </span>
      )}
    </div>
  );
}
