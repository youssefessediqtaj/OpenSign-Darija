import type { LightingLevel } from '../types/framing.types';

export function LightingIndicator({ lighting }: { lighting: LightingLevel }) {
  const label = lighting === 'too_dark' ? 'Eclairage faible' : lighting === 'acceptable' ? 'Eclairage acceptable' : 'Eclairage bon';
  return <p className="text-sm text-slate-700 dark:text-slate-300">{label}</p>;
}
