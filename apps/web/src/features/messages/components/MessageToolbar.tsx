import { useState } from 'react';

import { Button } from '../../../components/Button';

type Props = {
  onManualWord: (text: string) => void;
  onPunctuation: (mark: string) => void;
  onGenerate: () => void;
  onFinalize: () => void;
  generating: boolean;
};

export function MessageToolbar({ onManualWord, onPunctuation, onGenerate, onFinalize, generating }: Props) {
  const [manual, setManual] = useState('');
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap gap-2">
        <input className="min-h-11 flex-1 rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-950" value={manual} onChange={(event) => setManual(event.target.value)} placeholder="Mot manuel" aria-label="Mot manuel" />
        <Button onClick={() => { onManualWord(manual); setManual(''); }}>Ajouter</Button>
        <Button variant="secondary" onClick={() => onPunctuation('.')}>.</Button>
        <Button variant="secondary" onClick={() => onPunctuation('؟')}>؟</Button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button onClick={onGenerate} disabled={generating}>{generating ? 'Création de la phrase en Darija…' : 'Générer la phrase'}</Button>
        <Button variant="secondary" onClick={onFinalize}>Finaliser le message</Button>
      </div>
    </section>
  );
}
