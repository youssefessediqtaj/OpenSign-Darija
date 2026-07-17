import type { Message } from '../../../types/api';
import { SpeechButton } from '../../speech/components/SpeechButton';
import { MessageLanguageTabs } from './MessageLanguageTabs';
import { ShareMessageButton } from './ShareMessageButton';

export function MessageDetails({ message }: { message: Message }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <h2 className="font-semibold">{message.title || 'Message'}</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">{message.status} · version {message.generation_version}</p>
        </div>
        <ShareMessageButton message={message} />
      </div>
      <div className="mt-4">
        <MessageLanguageTabs message={message} />
      </div>
      <div className="mt-4">
        <SpeechButton message={message} />
      </div>
    </section>
  );
}
