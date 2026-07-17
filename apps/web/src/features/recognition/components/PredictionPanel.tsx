import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '../../../components/Button';
import { getOrCreateDraft, messagesApi } from '../../messages/services/messages-api.service';
import type { RecognitionResponse } from '../../../types/api';
import { landmarkRecognitionApi } from '../services/recognition-api.service';

export function PredictionPanel({ result }: { result: RecognitionResponse | null }) {
  const [selectedPredictionId, setSelectedPredictionId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const navigate = useNavigate();
  if (!result) {
    return (
      <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-xl font-semibold">Resultat</h2>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">Aucune sequence traitee pour le moment.</p>
      </aside>
    );
  }

  const top = result.predictions[0];
  if (!top) {
    return (
      <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
        <p className="text-sm font-semibold text-coral">Reconnaissance expérimentale d’un vocabulaire limité.</p>
        <h2 className="mt-3 text-xl font-semibold">Aucune prediction disponible.</h2>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          Le moteur a repondu sans proposition exploitable. Recommencez la capture ou reessayez plus tard.
        </p>
      </aside>
    );
  }
  const selected = result.predictions.find((prediction) => prediction.prediction_id === selectedPredictionId) ?? top;
  const decision = result.decision ?? 'known';
  const confidenceLevel = result.confidence_level ?? 'high';
  const isSensitive = ['MEDICAL', 'EMERGENCY', 'SENSITIVE'].includes(top.sign?.risk_level ?? '') || ['douleur', 'medecin', 'urgence', 'EMERGENCY'].includes(top.label);
  const title =
    decision === 'unknown'
      ? 'Signe non reconnu avec suffisamment de certitude.'
      : decision === 'uncertain'
        ? 'Le modele hesite. Verifiez les propositions.'
        : 'Signe propose';

  return (
    <aside className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
      <p className="text-sm font-semibold text-coral">Reconnaissance expérimentale d’un vocabulaire limité.</p>
      {result.inference_mode === 'mock' && (
        <p className="mt-2 text-sm font-medium text-amber-700">Mode developpement: resultat simule.</p>
      )}
      <h2 className="mt-3 text-xl font-semibold">{title}</h2>
      <div className="mt-4 rounded-md bg-slate-50 p-4 dark:bg-slate-800">
        <p className="text-2xl font-bold">{selected.sign?.french_translation ?? selected.label}</p>
        <p className="mt-2 text-2xl" lang="ar" dir="rtl">{selected.sign?.darija_arabic ?? '—'}</p>
        <p className="text-slate-700 dark:text-slate-300">{selected.sign?.darija_latin ?? selected.label}</p>
        <p className="mt-2 text-sm">Confiance {confidenceLevel}: {Math.round(selected.confidence * 100)} %</p>
      </div>
      {decision === 'unknown' && (
        <p className="mt-3 rounded-md border border-slate-300 bg-slate-50 p-3 text-sm text-slate-800">
          Le mouvement ne correspond pas avec suffisamment de certitude au vocabulaire actuel. Recommencez, choisissez une suggestion ou signalez un signe manquant.
        </p>
      )}
      {isSensitive && (
        <p className="mt-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
          Vérifiez ce résultat avant de l’utiliser. OpenSign Darija ne remplace pas un interprète professionnel.
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
      <dl className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300">
        <dt>Modele</dt><dd>{result.model_name}</dd>
        <dt>Version</dt><dd>{result.model_version}</dd>
        <dt>Schema</dt><dd>{result.feature_schema_version ?? '—'}</dd>
        <dt>Latence</dt><dd>{result.processing_time_ms} ms</dd>
      </dl>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          disabled={decision === 'unknown' || !selected.prediction_id}
          onClick={async () => {
            if (result.recognition_id && selected.prediction_id) {
              await landmarkRecognitionApi.confirm(result.recognition_id, selected.prediction_id);
              setConfirmed(true);
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
              setConfirmed(true);
            }
            setFeedback('Correction envoyee.');
          }}
        >
          Choisir cette proposition
        </Button>
        <Button
          variant="secondary"
          disabled={!confirmed || !result.recognition_id}
          onClick={async () => {
            if (!result.recognition_id) return;
            const draft = await getOrCreateDraft();
            const updated = await messagesApi.addItem(draft.id, {
              recognition_session_id: result.recognition_id,
              idempotency_key: `recognition-${result.recognition_id}`,
            });
            setFeedback('Signe ajoute au message.');
            navigate(`/app/messages/${updated.id}/edit`);
          }}
        >
          Ajouter au message
        </Button>
        <Button
          variant="secondary"
          disabled={!confirmed || !result.recognition_id}
          onClick={async () => {
            if (!result.recognition_id) return;
            const draft = await messagesApi.create('Message depuis reconnaissance');
            const updated = await messagesApi.addItem(draft.id, {
              recognition_session_id: result.recognition_id,
              idempotency_key: `recognition-${result.recognition_id}`,
            });
            navigate(`/app/messages/${updated.id}/edit`);
          }}
        >
          Créer un nouveau message
        </Button>
      </div>
      {feedback && <p className="mt-3 text-sm font-medium text-cedar">{feedback}</p>}
    </aside>
  );
}
