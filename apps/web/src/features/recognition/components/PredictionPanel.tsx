import { useState } from 'react';

import { Button } from '../../../components/Button';
import type { RecognitionResponse } from '../../../types/api';
import { landmarkRecognitionApi } from '../services/recognition-api.service';

export function PredictionPanel({ result }: { result: RecognitionResponse | null }) {
  const [selectedPredictionId, setSelectedPredictionId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  if (!result) {
    return (
      <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-xl font-semibold">Resultat</h2>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">Aucune sequence traitee pour le moment.</p>
      </aside>
    );
  }

  const top = result.predictions[0];
  const selected = result.predictions.find((prediction) => prediction.prediction_id === selectedPredictionId) ?? top;
  const isSensitive = ['MEDICAL', 'EMERGENCY'].includes(top.sign?.risk_level ?? '') || ['douleur', 'medecin', 'urgence'].includes(top.label);

  return (
    <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
      <p className="text-sm font-semibold text-coral">Resultat de demonstration — le modele reel n’est pas encore integre.</p>
      <h2 className="mt-3 text-xl font-semibold">Signe propose</h2>
      <div className="mt-4 rounded-md bg-slate-50 p-4 dark:bg-slate-800">
        <p className="text-2xl font-bold">{selected.sign?.french_translation ?? selected.label}</p>
        <p className="mt-2 text-2xl" lang="ar" dir="rtl">{selected.sign?.darija_arabic ?? '—'}</p>
        <p className="text-slate-700 dark:text-slate-300">{selected.sign?.darija_latin ?? selected.label}</p>
        <p className="mt-2 text-sm">Confiance: {Math.round(selected.confidence * 100)} %</p>
      </div>
      {isSensitive && (
        <p className="mt-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
          Ce resultat doit etre verifie. OpenSign Darija ne remplace pas un interprete professionnel ou un avis medical.
        </p>
      )}
      <h3 className="mt-5 font-semibold">Top 3</h3>
      <div className="mt-2 space-y-2">
        {result.predictions.map((prediction) => (
          <button
            key={prediction.rank}
            className="flex min-h-11 w-full items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-left hover:border-cedar dark:border-slate-700"
            onClick={() => setSelectedPredictionId(prediction.prediction_id ?? null)}
          >
            <span>{prediction.sign?.french_translation ?? prediction.label}</span>
            <span>{Math.round(prediction.confidence * 100)} %</span>
          </button>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          onClick={async () => {
            if (result.recognition_id && selected.prediction_id) {
              await landmarkRecognitionApi.confirm(result.recognition_id, selected.prediction_id);
              setFeedback('Prediction confirmee.');
            }
          }}
        >
          Confirmer
        </Button>
        <Button
          variant="secondary"
          onClick={async () => {
            if (result.recognition_id && selected.sign?.id) {
              await landmarkRecognitionApi.correct(result.recognition_id, selected.sign.id, 'none_of_these');
            }
            setFeedback('Aucun de ces signes signale.');
          }}
        >
          Aucun de ces signes
        </Button>
      </div>
      {feedback && <p className="mt-3 text-sm font-medium text-cedar">{feedback}</p>}
    </aside>
  );
}
