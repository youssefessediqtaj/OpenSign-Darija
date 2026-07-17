import type { Message } from '../../../types/api';
import { MessageItemCard } from './MessageItemCard';

type Props = {
  message: Message;
  onMove: (itemId: string, direction: -1 | 1) => void;
  onRemove: (itemId: string) => void;
};

export function MessageTimeline({ message, onMove, onRemove }: Props) {
  if (message.items.length === 0) {
    return <p className="rounded-md bg-slate-100 p-4 text-sm dark:bg-slate-800">Ajoutez un signe confirme ou un mot manuel.</p>;
  }
  return (
    <ol className="space-y-2" aria-label="Elements du message">
      {message.items.map((item, index) => (
        <MessageItemCard
          key={item.id}
          item={item}
          first={index === 0}
          last={index === message.items.length - 1}
          onMove={(direction) => onMove(item.id, direction)}
          onRemove={() => onRemove(item.id)}
        />
      ))}
    </ol>
  );
}
