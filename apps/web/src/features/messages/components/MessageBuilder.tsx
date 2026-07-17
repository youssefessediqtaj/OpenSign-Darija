import { useState } from 'react';

import { Button } from '../../../components/Button';
import type { Message } from '../../../types/api';
import { useMessageBuilder } from '../hooks/useMessageBuilder';
import { useMessageDraft } from '../hooks/useMessageDraft';
import { useMessageGeneration } from '../hooks/useMessageGeneration';
import { messagesApi } from '../services/messages-api.service';
import { exportMessageJson, exportMessageText } from '../services/message-export.service';
import { EmptyMessageState } from './EmptyMessageState';
import { FavoriteButton } from './FavoriteButton';
import { GeneratedMessagePanel } from './GeneratedMessagePanel';
import { GenerationSuggestions } from './GenerationSuggestions';
import { ManualTextEditor } from './ManualTextEditor';
import { MessageDetails } from './MessageDetails';
import { MessageTimeline } from './MessageTimeline';
import { MessageToolbar } from './MessageToolbar';
import { SemanticSequencePanel } from './SemanticSequencePanel';
import { ShareMessageButton } from './ShareMessageButton';

export function MessageBuilder({ initialMessage }: { initialMessage: Message | null }) {
  const [message, setMessage] = useState<Message | null>(initialMessage);
  const [error, setError] = useState<string | null>(null);
  const saveState = useMessageDraft(message, setMessage);
  const { addManualWord, addPunctuation, removeItem, moveItem } = useMessageBuilder(message, setMessage);
  const { generation, generating, generate } = useMessageGeneration(message, setMessage);

  async function create() {
    setMessage(await messagesApi.create());
  }

  async function finalize() {
    if (!message) return;
    try {
      const saved = await messagesApi.update(message.id, {
        final_darija_arabic: message.final_darija_arabic,
        final_darija_latin: message.final_darija_latin,
        final_french: message.final_french,
        final_english: message.final_english,
      });
      setMessage(await messagesApi.finalize(saved.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Finalisation impossible.');
    }
  }

  if (!message) return <EmptyMessageState onCreate={create} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Constructeur de message</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">Les phrases sont generees uniquement depuis les signes confirmes et les mots manuels marques.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <FavoriteButton
            active={message.is_favorite}
            onToggle={async () => setMessage(message.is_favorite ? await messagesApi.unfavorite(message.id) : await messagesApi.favorite(message.id))}
          />
          <ShareMessageButton message={message} />
        </div>
      </div>
      {!message.user_id && <p className="rounded-md bg-slate-100 p-3 text-sm dark:bg-slate-800">Connectez-vous pour conserver ce message dans votre compte.</p>}
      {message.risk_level !== 'NORMAL' && <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">Vérifiez attentivement ce message. OpenSign Darija ne remplace pas un interprète professionnel.</p>}
      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      <MessageToolbar onManualWord={addManualWord} onPunctuation={addPunctuation} onGenerate={generate} onFinalize={finalize} generating={generating} />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <MessageTimeline message={message} onMove={moveItem} onRemove={removeItem} />
          <ManualTextEditor message={message} saveState={saveState} onChange={(patch) => setMessage({ ...message, ...patch })} />
        </div>
        <div className="space-y-5">
          <SemanticSequencePanel message={message} />
          <GeneratedMessagePanel message={message} generation={generation} />
          <GenerationSuggestions generation={generation} />
          <MessageDetails message={message} />
          <section className="rounded-md border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900">
            <h2 className="font-semibold">Export</h2>
            <pre className="mt-2 max-h-40 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-white">{exportMessageJson(message)}</pre>
            <Button className="mt-3" variant="secondary" onClick={() => navigator.clipboard.writeText(exportMessageText(message))}>Copier export texte</Button>
          </section>
        </div>
      </div>
    </div>
  );
}
