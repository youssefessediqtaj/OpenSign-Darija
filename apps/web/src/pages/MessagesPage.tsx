import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../components/Button';
import { MessageBuilder } from '../features/messages/components/MessageBuilder';
import { MessageHistoryList } from '../features/messages/components/MessageHistoryList';
import { useCurrentMessage } from '../features/messages/hooks/useCurrentMessage';
import { messagesApi } from '../features/messages/services/messages-api.service';

export function MessagesHomePage() {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Messages Darija</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">Construisez, modifiez et retrouvez vos messages.</p>
        </div>
        <Link className="rounded-md bg-teal-700 px-4 py-2 text-white" to="/app/messages/new">Nouveau message</Link>
      </div>
      <MessageHistoryList />
    </div>
  );
}

export function NewMessagePage() {
  const navigate = useNavigate();
  useEffect(() => {
    messagesApi.create().then((message) => navigate(`/app/messages/${message.id}/edit`, { replace: true }));
  }, [navigate]);
  return <p>Creation du brouillon…</p>;
}

export function MessageEditPage() {
  const { messageId } = useParams();
  const { message, loading, error } = useCurrentMessage(messageId);
  if (loading) return <p>Chargement du message…</p>;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-red-800">{error}</p>;
  return <MessageBuilder initialMessage={message} />;
}

export function MessageDetailPage() {
  const { messageId } = useParams();
  const { message, loading, error } = useCurrentMessage(messageId);
  const [speech, setSpeech] = useState<string | null>(null);
  if (loading) return <p>Chargement du message…</p>;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-red-800">{error}</p>;
  if (!message) return <p>Message introuvable.</p>;
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{message.title || 'Message'}</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">{message.status}</p>
        </div>
        <div className="flex gap-2">
          <Link className="rounded-md bg-teal-700 px-4 py-2 text-white" to={`/app/messages/${message.id}/edit`}>Modifier</Link>
          <Button variant="secondary" disabled onClick={async () => setSpeech((await messagesApi.speech(message.id)).message)}>Parler — bientôt disponible</Button>
        </div>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-4xl font-semibold" lang="ar" dir="rtl">{message.final_darija_arabic || message.generated_darija_arabic}</p>
        <p className="mt-3 text-lg">{message.final_darija_latin || message.generated_darija_latin}</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{message.final_french || message.generated_french}</p>
      </section>
      {speech && <p className="rounded-md bg-slate-100 p-3 text-sm dark:bg-slate-800">{speech}</p>}
    </div>
  );
}

export function MessageHistoryPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Historique des messages</h1>
      <MessageHistoryList />
    </div>
  );
}

export function MessageFavoritesPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Messages favoris</h1>
      <MessageHistoryList favoriteOnly />
    </div>
  );
}
