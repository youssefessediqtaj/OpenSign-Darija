import { useMutation } from '@tanstack/react-query';
import { Camera, RotateCcw } from 'lucide-react';
import { useState } from 'react';

import { Button } from '../components/Button';
import { recognitionApi } from '../services/recognitionApi';

export function DemoPage() {
  const [authorized, setAuthorized] = useState(false);
  const mutation = useMutation({ mutationFn: recognitionApi.mock });
  const result = mutation.data;

  return (
    <section className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Demonstration simulee</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">Aucune video reelle n'est envoyee dans cette phase.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-md border border-slate-200 bg-slate-950 p-4 text-white dark:border-slate-800">
          <div className="flex aspect-video items-center justify-center rounded-md border border-dashed border-slate-600 bg-slate-900">
            <div className="text-center">
              <Camera className="mx-auto mb-3 h-10 w-10 text-teal-200" aria-hidden="true" />
              <p>{authorized ? 'Zone camera simulee prete' : 'Autorisation camera simulee requise'}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <Button onClick={() => setAuthorized(true)} variant="secondary">
              Autoriser la camera
            </Button>
            <Button onClick={() => mutation.mutate()} disabled={!authorized || mutation.isPending}>
              {mutation.isPending ? 'Analyse...' : 'Demarrer'}
            </Button>
            <Button variant="ghost" onClick={() => mutation.reset()}>
              <RotateCcw className="mr-2 inline h-4 w-4" aria-hidden="true" />
              Recommencer
            </Button>
          </div>
        </div>
        <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
          <h2 className="text-xl font-semibold">Resultat</h2>
          {!result && !mutation.isError && <p className="mt-4 text-slate-600 dark:text-slate-300">Aucun resultat pour le moment.</p>}
          {mutation.isError && <p className="mt-4 text-coral">Le service n'a pas repondu. Reessayez.</p>}
          {result && (
            <div className="mt-4 space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">Modele: {result.model_name} {result.model_version}</p>
              <ul className="space-y-3">
                {result.predictions.map((prediction) => (
                  <li key={prediction.rank} className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold">{prediction.label}</span>
                      <span>{Math.round(prediction.confidence * 100)}%</span>
                    </div>
                    <div className="mt-2 h-2 rounded bg-slate-200 dark:bg-slate-700">
                      <div className="h-2 rounded bg-cedar" style={{ width: `${prediction.confidence * 100}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
              <Button>Confirmer ce resultat</Button>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
