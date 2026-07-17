import type { GenerationResponse, Message } from '../../../types/api';

function statusLabel(status?: string) {
  if (status === 'INCOMPLETE') return 'Phrase incomplete';
  if (status === 'AMBIGUOUS') return 'Plusieurs formulations possibles';
  if (status === 'HIGH') return 'Phrase complete';
  return 'Controle linguistique limite';
}

export function GeneratedMessagePanel({ message, generation }: { message: Message; generation: GenerationResponse | null }) {
  const metadataStatus = String(message.generation_metadata.linguistic_status ?? '');
  const status = generation?.linguistic_status ?? metadataStatus;
  const warnings = generation?.warnings ?? (Array.isArray(message.generation_metadata.warnings) ? message.generation_metadata.warnings.map(String) : []);
  const alternatives = generation?.alternatives ?? (Array.isArray(message.generation_metadata.alternatives) ? message.generation_metadata.alternatives as Array<Record<string, string>> : []);
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Phrase generee</h2>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">{statusLabel(status)}</span>
      </div>
      <p className="mt-3 text-3xl font-semibold leading-relaxed" lang="ar" dir="rtl">{message.generated_darija_arabic || '—'}</p>
      <p className="mt-2 text-slate-700 dark:text-slate-300">{message.generated_darija_latin || '—'}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{message.generated_french || message.generated_english || 'Traduction facultative indisponible.'}</p>
      {warnings.map((warning) => (
        <p key={warning} className="mt-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">{warning}</p>
      ))}
      {alternatives.length > 1 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold">Alternatives</h3>
          <div className="mt-2 grid gap-2">
            {alternatives.map((alternative) => (
              <div key={alternative.template} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-800">
                <p lang="ar" dir="rtl">{alternative.darija_arabic}</p>
                <p>{alternative.darija_latin}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
