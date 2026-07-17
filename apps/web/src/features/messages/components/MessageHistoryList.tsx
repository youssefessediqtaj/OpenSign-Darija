import { useState } from 'react';

import { messagesApi } from '../services/messages-api.service';
import { useMessageHistory } from '../hooks/useMessageHistory';
import { MessageHistoryCard } from './MessageHistoryCard';

export function MessageHistoryList({ favoriteOnly = false }: { favoriteOnly?: boolean }) {
  const [query, setQuery] = useState('');
  const params = `?limit=20${favoriteOnly ? '&favorite=true' : ''}${query ? `&q=${encodeURIComponent(query)}` : ''}`;
  const { history, error, reload } = useMessageHistory(params);
  return (
    <section>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input className="min-h-11 rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-950" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher" aria-label="Rechercher un message" />
        <span className="text-sm text-slate-600 dark:text-slate-300">{history?.total ?? 0} messages</span>
      </div>
      {error && <p className="rounded-md bg-red-50 p-3 text-red-800">{error}</p>}
      <div className="space-y-3">
        {history?.items.map((message) => (
          <MessageHistoryCard
            key={message.id}
            message={message}
            onFavorite={async () => {
              if (message.is_favorite) await messagesApi.unfavorite(message.id);
              else await messagesApi.favorite(message.id);
              await reload();
            }}
            onDuplicate={async () => {
              await messagesApi.duplicate(message.id);
              await reload();
            }}
            onDelete={async () => {
              await messagesApi.delete(message.id);
              await reload();
            }}
          />
        ))}
      </div>
    </section>
  );
}
