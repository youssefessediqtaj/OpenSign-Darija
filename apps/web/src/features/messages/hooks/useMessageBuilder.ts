import type { Message } from '../../../types/api';
import { messagesApi } from '../services/messages-api.service';

export function useMessageBuilder(message: Message | null, setMessage: (message: Message) => void) {
  async function addManualWord(text: string) {
    if (!message || !text.trim()) return;
    setMessage(
      await messagesApi.addItem(message.id, {
        item_type: 'MANUAL_WORD',
        manual_text: text.trim(),
        idempotency_key: crypto.randomUUID(),
      }),
    );
  }

  async function addPunctuation(mark: string) {
    if (!message) return;
    setMessage(
      await messagesApi.addItem(message.id, {
        item_type: 'PUNCTUATION',
        manual_text: mark,
        idempotency_key: crypto.randomUUID(),
      }),
    );
  }

  async function removeItem(itemId: string) {
    if (!message) return;
    setMessage(await messagesApi.deleteItem(message.id, itemId));
  }

  async function moveItem(itemId: string, direction: -1 | 1) {
    if (!message) return;
    const ids = message.items.map((item) => item.id);
    const index = ids.indexOf(itemId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    setMessage(await messagesApi.reorder(message.id, ids));
  }

  return { addManualWord, addPunctuation, removeItem, moveItem };
}
