import { useCameraDevices } from '../features/recognition/hooks/useCameraDevices';
import { useRecognitionStore } from '../features/recognition/stores/recognition.store';
import type { CameraQuality, PerformanceMode } from '../features/recognition/types/camera.types';

export function SettingsPage() {
  const { preferences, updatePreferences, resetPreferences } = useRecognitionStore();
  const { devices } = useCameraDevices(true);

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-3xl font-bold">Parametres</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Preferences locales pour la capture de landmarks. Aucune sequence n’est stockee ici.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <span className="font-medium">Camera preferee</span>
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900"
            value={preferences.preferredDeviceId ?? ''}
            onChange={(event) => updatePreferences({ preferredDeviceId: event.target.value || null })}
          >
            <option value="">Camera frontale par defaut</option>
            {devices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <span className="font-medium">Mode performance</span>
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900"
            value={preferences.performanceMode}
            onChange={(event) => updatePreferences({ performanceMode: event.target.value as PerformanceMode })}
          >
            <option value="AUTO">AUTO</option>
            <option value="QUALITY">QUALITY</option>
            <option value="BALANCED">BALANCED</option>
            <option value="PERFORMANCE">PERFORMANCE</option>
          </select>
        </label>
        <label className="block rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <span className="font-medium">Qualite camera</span>
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900"
            value={preferences.cameraQuality}
            onChange={(event) => updatePreferences({ cameraQuality: event.target.value as CameraQuality })}
          >
            <option value="LOW">Basse</option>
            <option value="STANDARD">Standard</option>
            <option value="HIGH">Haute</option>
          </select>
        </label>
        <label className="block rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <span className="font-medium">Langue</span>
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900"
            value={preferences.language}
            onChange={(event) => updatePreferences({ language: event.target.value as 'fr' | 'ar' | 'en' })}
          >
            <option value="fr">Francais</option>
            <option value="ar">العربية</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {[
          ['showLandmarks', 'Afficher les landmarks'],
          ['batterySaver', 'Mode economie de batterie'],
          ['reduceMotion', 'Reduction des animations'],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <input
              type="checkbox"
              className="h-5 w-5"
              checked={Boolean(preferences[key as keyof typeof preferences])}
              onChange={(event) => updatePreferences({ [key]: event.target.checked })}
            />
            <span>{label}</span>
          </label>
        ))}
      </div>
      <button className="rounded-md border border-slate-300 px-4 py-2" onClick={resetPreferences}>
        Reinitialiser les preferences locales
      </button>
    </section>
  );
}
