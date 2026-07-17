import { ArrowLeft, Check, Delete, Space, X } from 'lucide-react';
import { useState } from 'react';

import { Button } from '../../../components/Button';
import type { RecognitionResponse } from '../../../types/api';
import { getOrCreateDraft, messagesApi } from '../../messages/services/messages-api.service';

const labelMap: Record<string, string> = {
  ARABIC_LETTER_ALEF: 'ا',
  ARABIC_LETTER_BAA: 'ب',
  ARABIC_LETTER_TAA: 'ت',
  ARABIC_LETTER_THAA: 'ث',
  ARABIC_LETTER_JEEM: 'ج',
};

type Props = {
  result: RecognitionResponse | null;
  isModelAvailable: boolean;
  isPending: boolean;
  onRecognize: () => void;
};

export function FingerspellingPanel({ result, isModelAvailable, isPending, onRecognize }: Props) {
  const [word, setWord] = useState('');
  const [manualLetter, setManualLetter] = useState('');
  const [status, setStatus] = useState('');
  const currentPrediction = result?.predictions[0];
  const currentLetter = currentPrediction ? labelMap[currentPrediction.label] ?? currentPrediction.label : '';
  const canConfirm =
    Boolean(currentLetter) &&
    !currentPrediction?.is_unknown &&
    (currentPrediction?.confidence ?? 0) >= 0.65;

  async function addWordToMessage() {
    const cleaned = word.trim();
    if (!cleaned) return;
    const draft = await getOrCreateDraft();
    await messagesApi.addItem(draft.id, {
      item_type: 'FINGERSPELLED_WORD',
      source: 'FINGERSPELLING',
      manual_text: cleaned,
      display_label: cleaned,
      idempotency_key: crypto.randomUUID(),
    });
    setStatus('Mot épelé ajouté au message.');
  }

  return (
    <section className="space-y-4 rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div>
        <h2 className="text-lg font-semibold">Alphabet / épellation</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Lettres confirmées une par une. Le mot épelé reste séparé des signes reconnus.
        </p>
      </div>
      {!isModelAvailable && (
        <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          Aucun modèle alphabet réel n’est actif. Le mode reste expérimental.
        </p>
      )}
      <Button type="button" onClick={onRecognize} disabled={isPending}>
        {isPending ? 'Analyse...' : 'Analyser la lettre stable'}
      </Button>
      {currentPrediction && (
        <div className="rounded-md bg-slate-50 p-3 dark:bg-slate-950">
          <p className="text-4xl font-bold" dir="rtl">
            {currentLetter}
          </p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            Confiance {Math.round(currentPrediction.confidence * 100)}%
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {result.predictions.slice(0, 3).map((prediction) => (
              <span key={prediction.rank} className="rounded-md bg-white px-2 py-1 dark:bg-slate-800">
                {labelMap[prediction.label] ?? prediction.label} · {Math.round(prediction.confidence * 100)}%
              </span>
            ))}
          </div>
          <Button
            type="button"
            className="mt-3 inline-flex items-center gap-2"
            disabled={!canConfirm}
            onClick={() => setWord((current) => `${current}${currentLetter}`)}
          >
            <Check size={18} aria-hidden="true" />
            Confirmer
          </Button>
        </div>
      )}
      <div className="space-y-2">
        <label className="text-sm font-semibold" htmlFor="manual-letter">
          Lettre manuelle
        </label>
        <div className="flex gap-2">
          <input
            id="manual-letter"
            className="min-h-11 w-28 rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-950"
            value={manualLetter}
            maxLength={2}
            onChange={(event) => setManualLetter(event.target.value)}
          />
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              if (manualLetter.trim()) setWord((current) => `${current}${manualLetter.trim()}`);
              setManualLetter('');
            }}
          >
            Ajouter
          </Button>
        </div>
      </div>
      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
        <p className="text-sm font-semibold">Mot</p>
        <p className="min-h-12 py-2 text-3xl font-bold" dir="rtl">
          {word || ' '}
        </p>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => setWord((current) => current.slice(0, -1))}>
            <Delete size={18} aria-hidden="true" />
          </Button>
          <Button type="button" variant="secondary" onClick={() => setWord((current) => `${current} `)}>
            <Space size={18} aria-hidden="true" />
          </Button>
          <Button type="button" variant="secondary" onClick={() => setWord('')}>
            <X size={18} aria-hidden="true" />
          </Button>
          <Button type="button" variant="secondary" onClick={() => setWord((current) => current.trim())}>
            <ArrowLeft size={18} aria-hidden="true" />
          </Button>
        </div>
      </div>
      <Button type="button" disabled={!word.trim()} onClick={addWordToMessage}>
        Ajouter au message
      </Button>
      {status && <p className="text-sm text-cedar">{status}</p>}
    </section>
  );
}
