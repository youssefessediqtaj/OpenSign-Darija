import { Button } from '../../../components/Button';
import type { MessageItem } from '../../../types/api';

type Props = {
  item: MessageItem;
  first: boolean;
  last: boolean;
  onMove: (direction: -1 | 1) => void;
  onRemove: () => void;
};

export function MessageItemCard({ item, first, last, onMove, onRemove }: Props) {
  return (
    <li className="rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{item.display_label}</p>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            {item.semantic_concept_code ?? item.item_type} · {item.source}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" disabled={first} onClick={() => onMove(-1)} aria-label="Monter l'element">↑</Button>
          <Button variant="secondary" disabled={last} onClick={() => onMove(1)} aria-label="Descendre l'element">↓</Button>
          <Button variant="secondary" onClick={onRemove}>Supprimer</Button>
        </div>
      </div>
    </li>
  );
}
