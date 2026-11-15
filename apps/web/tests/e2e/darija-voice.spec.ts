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
  await page.goto('/app/recognition?diagnostics=1');
  const tester = page.getByRole('region', { name: 'Test local du pack vocal' });
  await expect(tester).toBeVisible();
  await expect(tester.locator('[lang="ary"]')).toHaveAttribute('dir', 'rtl');
  expect(audioRequests).toHaveLength(0);
  await tester.getByRole('button', { name: 'Écouter en darija' }).click();
  await expect(tester.getByRole('status')).toHaveText('Lecture en cours.');
  expect(audioRequests).toHaveLength(1);
  await tester.getByLabel('Test local du pack vocal (sans caméra)').selectOption('red');
  await expect(tester.getByRole('status')).toHaveText('Lecture arrêtée.');
  await tester.getByRole('button', { name: 'Écouter en darija' }).click();
  await expect(tester.getByRole('status')).toContainText('indisponible');
  await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeVisible();
  expect(errors).toEqual([]);
});
