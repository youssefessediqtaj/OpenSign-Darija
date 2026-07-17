import { apiRequest } from '../../../lib/api';
import type {
  GenerationResponse,
  Message,
  MessageList,
  MessageRevision,
  LinguisticTemplate,
  SemanticConcept,
} from '../../../types/api';

const SESSION_KEY = 'opensign.guestSessionId';

export function getGuestSessionId() {
  const existing = window.localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(SESSION_KEY, created);
  return created;
}

export function guestHeaders() {
  return { 'X-Anonymous-Session-Id': getGuestSessionId() };
}

export const messagesApi = {
  create: (title = 'Nouveau message') =>
    apiRequest<Message>('/api/v1/messages', {
      method: 'POST',
      headers: guestHeaders(),
      body: JSON.stringify({ anonymous_session_id: getGuestSessionId(), title }),
    }),
  list: (params = '') =>
    apiRequest<MessageList>(`/api/v1/messages${params}`, { headers: guestHeaders() }),
  get: (id: string) => apiRequest<Message>(`/api/v1/messages/${id}`, { headers: guestHeaders() }),
  update: (id: string, payload: Partial<Message>) =>
    apiRequest<Message>(`/api/v1/messages/${id}`, {
      method: 'PATCH',
      headers: guestHeaders(),
      body: JSON.stringify(payload),
    }),
  delete: (id: string) =>
    apiRequest<{ status: string }>(`/api/v1/messages/${id}`, {
      method: 'DELETE',
      headers: guestHeaders(),
    }),
  archive: (id: string) =>
    apiRequest<Message>(`/api/v1/messages/${id}/archive`, {
      method: 'POST',
      headers: guestHeaders(),
    }),
  duplicate: (id: string) =>
    apiRequest<Message>(`/api/v1/messages/${id}/duplicate`, {
      method: 'POST',
      headers: guestHeaders(),
    }),
  favorite: (id: string) =>
    apiRequest<Message>(`/api/v1/messages/${id}/favorite`, {
      method: 'POST',
      headers: guestHeaders(),
    }),
  unfavorite: (id: string) =>
    apiRequest<Message>(`/api/v1/messages/${id}/favorite`, {
      method: 'DELETE',
      headers: guestHeaders(),
    }),
  addItem: (id: string, payload: Record<string, unknown>) =>
    apiRequest<Message>(`/api/v1/messages/${id}/items`, {
      method: 'POST',
      headers: guestHeaders(),
      body: JSON.stringify(payload),
    }),
  updateItem: (messageId: string, itemId: string, payload: Record<string, unknown>) =>
    apiRequest<Message>(`/api/v1/messages/${messageId}/items/${itemId}`, {
      method: 'PATCH',
      headers: guestHeaders(),
      body: JSON.stringify(payload),
    }),
  deleteItem: (messageId: string, itemId: string) =>
    apiRequest<Message>(`/api/v1/messages/${messageId}/items/${itemId}`, {
      method: 'DELETE',
      headers: guestHeaders(),
    }),
  reorder: (id: string, itemIds: string[]) =>
    apiRequest<Message>(`/api/v1/messages/${id}/items/reorder`, {
      method: 'POST',
      headers: guestHeaders(),
      body: JSON.stringify({ item_ids: itemIds, idempotency_key: crypto.randomUUID() }),
    }),
  generate: (id: string) =>
    apiRequest<GenerationResponse>(`/api/v1/messages/${id}/generate`, {
      method: 'POST',
      headers: guestHeaders(),
      body: JSON.stringify({ idempotency_key: crypto.randomUUID() }),
    }),
  finalize: (id: string) =>
    apiRequest<Message>(`/api/v1/messages/${id}/finalize`, {
      method: 'POST',
      headers: guestHeaders(),
    }),
  revisions: (id: string) =>
    apiRequest<MessageRevision[]>(`/api/v1/messages/${id}/revisions`, {
      headers: guestHeaders(),
    }),
  speech: (id: string) =>
    apiRequest<{ status: string; message: string; contract: Record<string, unknown> }>(
      `/api/v1/messages/${id}/speech/prepare`,
      {
        method: 'POST',
        headers: guestHeaders(),
        body: JSON.stringify({ language: 'ary-MA', voice: 'default', speed: 1 }),
      },
    ),
  concepts: () => apiRequest<SemanticConcept[]>('/api/v1/linguistics/concepts'),
  templates: () => apiRequest<LinguisticTemplate[]>('/api/v1/linguistics/templates'),
};

export async function getOrCreateDraft() {
  const list = await messagesApi.list('?status=DRAFT&limit=1');
  return list.items[0] ?? messagesApi.create();
}
