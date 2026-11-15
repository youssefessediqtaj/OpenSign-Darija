import { expect, test } from '@playwright/test';

// Test-only silent PCM; never installed as a voice recording.
function fixtureWav(): string {
  const bytes = new Uint8Array(44 + 8192 * 2);
  const view = new DataView(bytes.buffer);
  const write = (offset: number, value: string) => [...value].forEach((char, i) => { bytes[offset + i] = char.charCodeAt(0); });
  write(0, 'RIFF'); view.setUint32(4, bytes.length - 8, true); write(8, 'WAVEfmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 8224, true); view.setUint32(28, 16448, true); view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); write(36, 'data'); view.setUint32(40, 8192 * 2, true);
  return Array.from(bytes, (byte) => String.fromCharCode(byte)).join('');
}

test('local voice tester plays manually without camera and cancels on color change', async ({ page }) => {
  const errors: string[] = [];
  const audioRequests: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.setViewportSize({ width: 375, height: 800 });
  await page.route('**/audio/darija/colors/*.wav', async (route) => {
    audioRequests.push(route.request().url());
    if (route.request().url().endsWith('/black.wav')) {
      await route.fulfill({ status: 200, contentType: 'audio/wav', body: fixtureWav() });
    } else {
      await route.fulfill({ status: 404, body: '' });
    }
  });
  await page.route(/approved-voice-pack\.json(?:\?.*)?$/, async (route) => route.fulfill({ contentType: 'application/javascript', body: `export default { version: '1', assets: { black: { approved: true, expression: 'كحل', sha256: '${'a'.repeat(64)}', version: 'fixture' }, red: { approved: true, expression: 'حمر', sha256: '${'a'.repeat(64)}', version: 'fixture' } } };` }));
  await page.goto('/app/recognition?diagnostics=1');
  const tester = page.getByRole('region', { name: 'Test local du pack vocal' });
  await expect(tester).toBeVisible();
  await expect(tester.locator('[lang="ary"]')).toHaveAttribute('dir', 'rtl');
  expect(audioRequests).toHaveLength(0);
  await tester.getByRole('button', { name: 'Écouter en darija' }).click();
  await expect(tester.getByRole('region', { name: 'Aperçu vocal Darija' }).getByRole('status')).toHaveText('Lecture en cours.');
  expect(audioRequests).toHaveLength(1);
  await tester.getByLabel('Test local du pack vocal (sans caméra)').selectOption('red');
  await expect(tester.getByRole('region', { name: 'Aperçu vocal Darija' }).getByRole('status')).toHaveText('Lecture arrêtée.');
  await tester.getByRole('button', { name: 'Écouter en darija' }).click();
  await expect(tester.getByRole('region', { name: 'Aperçu vocal Darija' }).getByRole('status')).toContainText('indisponible');
  await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('unapproved voice pack never requests or plays a clip', async ({ page }) => {
  const audioRequests: string[] = [];
  page.on('request', (request) => { if (request.url().includes('/audio/darija/colors/')) audioRequests.push(request.url()); });
  await page.goto('/app/recognition?diagnostics=1');
  const tester = page.getByRole('region', { name: 'Test local du pack vocal' });
  await expect(tester).toContainText('Audio non approuvé ou absent');
  await tester.getByRole('button', { name: 'Écouter en darija' }).click();
  await expect(tester.getByRole('region', { name: 'Aperçu vocal Darija' }).getByRole('status')).toContainText('indisponible');
  expect(audioRequests).toEqual([]);
});


test('private file tester accepts nine files locally and clears on invalid selection', async ({ page }) => {
  const audioRequests: string[] = [];
  page.on('request', (request) => { if (request.url().includes('/audio/darija/colors/')) audioRequests.push(request.url()); });
  await page.goto('/app/recognition?diagnostics=1');
  const panel = page.getByRole('region', { name: 'Aperçu privé des enregistrements' });
  await panel.locator('input[type=file]').evaluate((input: HTMLInputElement) => {
    const transfer = new DataTransfer();
    for (const color of ['black', 'blue', 'brown', 'green', 'orange', 'pink', 'red', 'white', 'yellow']) {
      transfer.items.add(new File(['test only'], `${color}.wav`, { type: 'audio/wav' }));
    }
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await expect(panel.getByRole('status')).toContainText('Aperçu privé uniquement');
  await expect(panel.locator('audio')).toHaveAttribute('src', /^blob:/);
  await panel.getByLabel('Couleur à écouter').selectOption('red');
  await expect(panel.locator('[lang=ary]')).toHaveText('حمر');
  await expect(panel.getByLabel('Enregistrement privé red')).toBeVisible();
  expect(audioRequests).toEqual([]);
  await panel.locator('input[type=file]').evaluate((input: HTMLInputElement) => {
    const transfer = new DataTransfer();
    transfer.items.add(new File(['bad'], '../bad.wav'));
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await expect(panel.getByRole('status')).toContainText('invalides');
  await expect(panel.locator('audio')).toHaveCount(0);
});
