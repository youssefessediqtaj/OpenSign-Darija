import { CheckCircle2 } from 'lucide-react';

import type { ContributionReceipt } from '../types';

export function ContributionSuccess({ receipt }: { receipt: ContributionReceipt }) {
  return (
    <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-6" role="status">
      <CheckCircle2 className="h-10 w-10 text-emerald-700" aria-hidden="true" />
      <h2 className="mt-3 text-2xl font-bold text-emerald-950">Contribution reçue</h2>
      <p className="mt-2 text-emerald-950">
        Merci. Votre contribution a été reçue et sera vérifiée avant toute utilisation pour
        l’entraînement.
      </p>
      <p className="mt-4 font-semibold">
        Référence : <code data-testid="contribution-id">{receipt.contribution_id}</code>
      </p>
      <p className="mt-2 text-sm">{receipt.deletion_request_instructions}</p>
    </section>
  );
}
