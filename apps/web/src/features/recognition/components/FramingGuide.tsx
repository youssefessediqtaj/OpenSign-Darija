import type { FramingEvaluation } from '../types/framing.types';
import { framingInstruction } from '../utils/framing-evaluator';

export function FramingGuide({ evaluation }: { evaluation: FramingEvaluation }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
      <h2 className="font-semibold">Cadrage</h2>
      <p className="mt-2 text-sm">{framingInstruction(evaluation)}</p>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
        <div><dt>Visage</dt><dd>{evaluation.faceVisible ? 'visible' : 'absent'}</dd></div>
        <div><dt>Main gauche</dt><dd>{evaluation.leftHandVisible ? 'visible' : 'absente'}</dd></div>
        <div><dt>Main droite</dt><dd>{evaluation.rightHandVisible ? 'visible' : 'absente'}</dd></div>
        <div><dt>Lumiere</dt><dd>{evaluation.lighting}</dd></div>
        <div><dt>Distance</dt><dd>{evaluation.distance}</dd></div>
        <div><dt>Stabilite</dt><dd>{evaluation.stability}</dd></div>
      </dl>
    </div>
  );
}
