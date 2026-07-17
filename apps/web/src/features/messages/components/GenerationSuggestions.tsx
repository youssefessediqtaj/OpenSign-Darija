import type { GenerationResponse } from '../../../types/api';

export function GenerationSuggestions({ generation }: { generation: GenerationResponse | null }) {
  if (!generation || generation.linguistic_status === 'HIGH') return null;
  return (
    <section className="rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
      <h2 className="font-semibold">Suggestions</h2>
      {generation.linguistic_status === 'INCOMPLETE' && <p className="mt-2">Continuez la reconnaissance, ajoutez un objet ou gardez le mot seul.</p>}
      {generation.linguistic_status === 'AMBIGUOUS' && <p className="mt-2">Choisissez une formulation dans les alternatives avant de finaliser si nécessaire.</p>}
    </section>
  );
}
