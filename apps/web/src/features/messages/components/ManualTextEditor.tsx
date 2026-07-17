import type { Message } from '../../../types/api';

type Props = {
  message: Message;
  onChange: (patch: Partial<Message>) => void;
  saveState: string;
};

export function ManualTextEditor({ message, onChange, saveState }: Props) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-semibold">Edition finale</h2>
        <span className="text-xs text-slate-600 dark:text-slate-300">{saveState === 'SAVING' ? 'Enregistrement…' : saveState === 'ERROR' ? 'Erreur de sauvegarde' : 'Enregistré'}</span>
      </div>
      <label className="mt-3 block text-sm font-medium" htmlFor="final-ar">Darija arabe</label>
      <textarea
        id="final-ar"
        dir="rtl"
        lang="ar"
        className="mt-1 min-h-24 w-full rounded-md border border-slate-300 bg-white p-3 text-xl dark:border-slate-700 dark:bg-slate-950"
        value={message.final_darija_arabic ?? ''}
        onChange={(event) => onChange({ final_darija_arabic: event.target.value })}
      />
      <label className="mt-3 block text-sm font-medium" htmlFor="final-latin">Darija latine</label>
      <textarea id="final-latin" className="mt-1 min-h-20 w-full rounded-md border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" value={message.final_darija_latin ?? ''} onChange={(event) => onChange({ final_darija_latin: event.target.value })} />
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <textarea aria-label="Traduction francaise" className="min-h-16 rounded-md border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" value={message.final_french ?? ''} onChange={(event) => onChange({ final_french: event.target.value })} />
        <textarea aria-label="Traduction anglaise" className="min-h-16 rounded-md border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" value={message.final_english ?? ''} onChange={(event) => onChange({ final_english: event.target.value })} />
      </div>
      <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">Modifier l’arabe ne remplace pas automatiquement la transcription latine.</p>
    </section>
  );
}
