import { expect, test } from '@playwright/test';

function now() {
  return '2026-07-17T00:00:00Z';
}

test('guest can build, edit, finalize and find a Darija message', async ({ page }) => {
  const message = {
    id: 'msg-e2e',
    anonymous_session_id: 'guest',
    status: 'DRAFT',
    title: 'Nouveau message',
    raw_semantic_sequence: [] as string[],
    generated_darija_arabic: '',
    generated_darija_latin: '',
    generated_french: '',
    generated_english: '',
    final_darija_arabic: '',
    final_darija_latin: '',
    final_french: '',
    final_english: '',
    generation_strategy: 'template_rules',
    generation_version: '1.0.0',
    generation_metadata: {},
    is_favorite: false,
    item_count: 0,
    risk_level: 'NORMAL',
    items: [] as Array<Record<string, unknown>>,
    created_at: now(),
    updated_at: now(),
    completed_at: null as string | null,
  };

  await page.route('**/api/v1/messages**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (request.method() === 'POST' && path === '/api/v1/messages') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
    }
    if (request.method() === 'GET' && path === '/api/v1/messages/msg-e2e') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
    }
    if (request.method() === 'POST' && path === '/api/v1/messages/msg-e2e/items') {
      const body = await request.postDataJSON();
      message.items.push({
        id: `item-${message.items.length + 1}`,
        position: message.items.length + 1,
        item_type: body.item_type,
        source: 'MANUAL_INPUT',
        display_label: body.manual_text,
        metadata: {},
        created_at: now(),
      });
      message.item_count = message.items.length;
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
    }
    if (request.method() === 'POST' && path === '/api/v1/messages/msg-e2e/generate') {
      message.generated_darija_arabic = 'بغيت الما';
      message.generated_darija_latin = 'bghit lma';
      message.final_darija_arabic = 'بغيت الما';
      message.final_darija_latin = 'bghit lma';
      message.raw_semantic_sequence = ['ACTION_WANT', 'OBJECT_WATER'];
      message.generation_metadata = { linguistic_status: 'HIGH', warnings: [], alternatives: [] };
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message_id: message.id,
          generation_version: '1.0.0',
          strategy: 'template_rules',
          semantic_sequence: message.raw_semantic_sequence,
          result: {
            darija_arabic: 'بغيت الما',
            darija_latin: 'bghit lma',
            french: "Je veux de l'eau.",
            english: 'I want water.',
          },
          template: 'WANT_OBJECT',
          linguistic_status: 'HIGH',
          system_insertions: [],
          warnings: [],
          alternatives: [],
        }),
      });
    }
    if (request.method() === 'PATCH' && path === '/api/v1/messages/msg-e2e') {
      Object.assign(message, await request.postDataJSON());
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
    }
    if (request.method() === 'POST' && path === '/api/v1/messages/msg-e2e/finalize') {
      message.status = 'COMPLETED';
      message.completed_at = now();
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
    }
    if (request.method() === 'GET' && path === '/api/v1/messages') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [message], total: 1, limit: 20, offset: 0 }),
      });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(message) });
  });

  await page.goto('/app/messages/new');
  await expect(page.getByRole('heading', { name: /Constructeur de message/i })).toBeVisible();
  await page.getByLabel('Mot manuel').fill('eau');
  await page.getByRole('button', { name: /^Ajouter$/i }).click();
  await expect(page.getByText('eau', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /Générer la phrase/i }).click();
  await expect(page.getByLabel(/Darija arabe/i)).toHaveValue('بغيت الما');
  await page.getByLabel(/Darija arabe/i).fill('بغيت الما دابا');
  await expect(page.getByLabel(/Darija latine/i)).toHaveValue('bghit lma');
  await page.waitForTimeout(900);
  await page.getByRole('button', { name: /Finaliser le message/i }).click();
  await expect(page.getByText(/COMPLETED/i)).toBeVisible();
  await page.goto('/app/messages/history');
  await expect(page.getByText('بغيت الما دابا')).toBeVisible();
});
