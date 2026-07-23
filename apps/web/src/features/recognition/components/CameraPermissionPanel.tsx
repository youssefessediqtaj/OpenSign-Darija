import { Camera } from 'lucide-react';

import { Button } from '../../../shared/ui/Button';

export function CameraPermissionPanel({
  onEnable,
  errorMessage,
  isRequesting,
}: {
  onEnable: () => void;
  errorMessage: string | null;
  isRequesting: boolean;
}) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start gap-3">
        <Camera className="mt-1 h-6 w-6 text-cedar" aria-hidden="true" />
        <div>
          <h2 className="text-xl font-semibold">Activer la caméra</h2>
          <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
            La vidéo est analysée directement sur votre appareil. Seuls les points de mouvement
            nécessaires à la reconnaissance sont transmis au serveur. Aucune vidéo n’est enregistrée
            dans cette version.
          </p>
        </div>
      </div>
      {errorMessage && (
        <p className="mt-4 rounded-md border border-coral bg-red-50 p-3 text-sm font-medium text-coral" role="alert">
          {errorMessage}
        </p>
      )}
      <Button className="mt-5 w-full sm:w-auto" onClick={onEnable} disabled={isRequesting}>
        {isRequesting ? 'Demande en cours…' : 'Activer la caméra'}
      </Button>
    </section>
  );
}
