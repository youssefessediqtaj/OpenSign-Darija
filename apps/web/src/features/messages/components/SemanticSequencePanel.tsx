import type { Message } from '../../../types/api';

export function SemanticSequencePanel({ message }: { message: Message }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="font-semibold">Sequence semantique</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {message.raw_semantic_sequence.length ? (
          message.raw_semantic_sequence.map((item, index) => (
            <span key={`${item}-${index}`} className="rounded-md bg-teal-100 px-3 py-1 text-sm text-teal-950">
              {String(item)}
            </span>
          ))
        ) : (
          <span className="text-sm text-slate-600 dark:text-slate-300">Aucun concept confirme.</span>
        )}
      </div>
    </section>
  );
}
