import { useEffect, useState } from 'react';

import type { SpeechVoice } from '../types/api';
import { speechApi } from '../features/speech/services/speech-api.service';

export function SpeechAdminPage() {
  const [voices, setVoices] = useState<SpeechVoice[]>([]);
  const [status, setStatus] = useState<string>('Chargement');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([speechApi.voices(), speechApi.status()])
      .then(([voiceResponse, statusResponse]) => {
        if (cancelled) return;
        setVoices(voiceResponse.voices);
        setStatus(statusResponse.service_available ? 'READY' : 'DEGRADED');
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Statut speech indisponible.');
          setStatus('FAILED');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Administration speech</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">Voix, licences, versions et etat du service vocal interne.</p>
      </div>
      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="font-semibold">Statut</h2>
        <p className="mt-2 text-sm">{status}</p>
      </section>
      <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="font-semibold">Voix</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800">
                <th className="py-2">Nom</th>
                <th>Locale</th>
                <th>Provider</th>
                <th>Version</th>
                <th>Licence</th>
              </tr>
            </thead>
            <tbody>
              {voices.map((voice) => (
                <tr key={voice.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">{voice.display_name}</td>
                  <td>{voice.locale}</td>
                  <td>{voice.provider}</td>
                  <td>{voice.model_version}</td>
                  <td>{String(voice.license_info.license ?? 'UNCONFIRMED')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
