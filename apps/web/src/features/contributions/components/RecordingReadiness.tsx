import { CheckCircle2, Circle } from 'lucide-react';

import type { ReadinessChecks } from '../domain/readiness-policy';

export function RecordingReadiness({ readiness }: { readiness: ReadinessChecks }) {
  const items = [
    ['Détecteur prêt', readiness.detectorReady],
    ['Visage visible (cadrage uniquement)', readiness.faceVisible],
    ['Main gauche visible', readiness.leftHandVisible],
    ['Main droite visible', readiness.rightHandVisible],
    ['Haut du corps cadré', readiness.upperBodyFramed],
    ['Éclairage et distance acceptables', readiness.adequateLighting && readiness.acceptableDistance],
    ['Position stable', readiness.stable],
  ] as const;
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4" aria-labelledby="readiness-title">
      <h3 id="readiness-title" className="font-semibold">
        Préparation de l’enregistrement
      </h3>
      <p className="mt-2 text-sm font-semibold text-slate-700" role="status" aria-live="polite">
        {readiness.guidance}
      </p>
      <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        {items.map(([label, passed]) => (
          <li key={label} className="flex items-center gap-2">
            {passed ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            ) : (
              <Circle className="h-4 w-4 text-slate-300" aria-hidden="true" />
            )}
            {label}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-slate-500">
        Cette vérification détecte seulement la visibilité et le cadrage. Elle n’identifie jamais
        la personne et ne crée aucune empreinte faciale.
      </p>
    </section>
  );
}
