import { Button } from '../../../components/Button';

export function CameraControls({
  canCapture,
  isCameraActive,
  isCapturing,
  isSubmitting,
  onStartCamera,
  onStopCamera,
  onStartCapture,
  onFinishCapture,
  onCancelCapture,
  showLandmarks,
  onToggleLandmarks,
}: {
  canCapture: boolean;
  isCameraActive: boolean;
  isCapturing: boolean;
  isSubmitting: boolean;
  onStartCamera: () => void;
  onStopCamera: () => void;
  onStartCapture: () => void;
  onFinishCapture: () => void;
  onCancelCapture: () => void;
  showLandmarks: boolean;
  onToggleLandmarks: () => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      {isCameraActive ? (
        <Button variant="secondary" onClick={onStopCamera} disabled={isCapturing || isSubmitting}>
          Desactiver la camera
        </Button>
      ) : (
        <Button onClick={onStartCamera}>Activer la camera</Button>
      )}
      {!isCapturing ? (
        <Button onClick={onStartCapture} disabled={!canCapture || isSubmitting}>
          Commencer
        </Button>
      ) : (
        <Button onClick={onFinishCapture}>Terminer</Button>
      )}
      <Button variant="ghost" onClick={onCancelCapture} disabled={!isCapturing && !isSubmitting}>
        Annuler
      </Button>
      <Button variant="ghost" onClick={onToggleLandmarks}>
        {showLandmarks ? 'Masquer les points' : 'Afficher les points de mouvement'}
      </Button>
    </div>
  );
}
