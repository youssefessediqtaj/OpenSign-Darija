import { Link } from 'react-router-dom';

import type { Message } from '../../../types/api';
import { FavoriteButton } from './FavoriteButton';

type Props = {
  message: Message;
  onFavorite: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
};

export function MessageHistoryCard({ message, onFavorite, onDuplicate, onDelete }: Props) {
  const preview = message.final_darija_arabic || message.generated_darija_arabic || 'Message sans texte';
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <p className="text-lg font-semibold" dir="rtl" lang="ar">{preview}</p>
          <p className="text-sm text-slate-600 dark:text-slate-300">{message.status} · {message.item_count} elements · {message.risk_level}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white" to={`/app/messages/${message.id}`}>Ouvrir</Link>
          <FavoriteButton active={message.is_favorite} onToggle={onFavorite} />
          <button className="rounded-md border px-3 py-2 text-sm" onClick={onDuplicate}>Dupliquer</button>
          <button className="rounded-md border px-3 py-2 text-sm" onClick={onDelete}>Supprimer</button>
        </div>
      </div>
    </article>
  );
}
