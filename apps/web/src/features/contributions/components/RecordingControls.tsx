import { Camera, CircleDot, RotateCcw, Square, Upload } from 'lucide-react';

import { Button } from '../../../shared/ui/Button';

export function RecordingControls({
  cameraActive,
  canActivateCamera,
  canRecord,
  isRecording,
  hasPreview,
  canSubmit,
  uploading,
  elapsedSeconds,
  onActivateCamera,
  onStopCamera,
  onRecord,
  onStopRecording,
  onRetake,
  onSubmit,
}: {
  cameraActive: boolean;
  canActivateCamera: boolean;
  canRecord: boolean;
  isRecording: boolean;
  hasPreview: boolean;
  canSubmit: boolean;
  uploading: boolean;
  elapsedSeconds: number;
  onActivateCamera: () => void;
  onStopCamera: () => void;
  onRecord: () => void;
  onStopRecording: () => void;
  onRetake: () => void;
  onSubmit: () => void;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      {isRecording && (
        <p className="mb-3 font-mono text-lg font-bold text-red-700" role="timer">
          ● {elapsedSeconds.toFixed(1)} s
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        {!cameraActive && (
          <Button type="button" disabled={!canActivateCamera} onClick={onActivateCamera}>
            <Camera className="mr-2 inline h-5 w-5" aria-hidden="true" />
            Activer la caméra
          </Button>
        )}
        {cameraActive && !isRecording && !hasPreview && (
          <Button type="button" disabled={!canRecord} onClick={onRecord}>
            <CircleDot className="mr-2 inline h-5 w-5" aria-hidden="true" />
            Enregistrer
          </Button>
        )}
        {isRecording && (
          <Button type="button" onClick={onStopRecording}>
            <Square className="mr-2 inline h-5 w-5" aria-hidden="true" />
            Arrêter
          </Button>
        )}
        {hasPreview && !isRecording && (
          <>
            <Button type="button" variant="secondary" onClick={onRetake}>
              <RotateCcw className="mr-2 inline h-5 w-5" aria-hidden="true" />
              Recommencer
            </Button>
            <Button type="button" disabled={!canSubmit || uploading} onClick={onSubmit}>
              <Upload className="mr-2 inline h-5 w-5" aria-hidden="true" />
              {uploading ? 'Envoi en cours…' : 'Envoyer ma contribution'}
            </Button>
          </>
        )}
        {cameraActive && !isRecording && (
          <Button type="button" variant="ghost" onClick={onStopCamera}>
            Éteindre la caméra
          </Button>
        )}
      </div>
    </section>
  );
}
