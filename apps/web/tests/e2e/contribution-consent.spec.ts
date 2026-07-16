import { expect, test } from '@playwright/test';

test('contribution consents are explicit in the browser', async ({ page }) => {
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
      }),
    });
  });
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-1',
        email: 'contributor@example.test',
        display_name: 'Contributor Demo',
        roles: ['USER', 'CONTRIBUTOR'],
      }),
    });
  });
  await page.route('**/api/v1/consents/templates', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'template-1',
          code: 'dataset-collection',
          version: '1.0.0',
          language: 'fr',
          title: 'Consentement dataset',
          summary: 'Choix separes',
          full_text: 'Texte complet',
          is_active: true,
        },
      ]),
    });
  });
  await page.route('**/api/v1/consents/me', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
  });

  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => {
          window.localStorage.setItem('camera-requested', '1');
          throw new DOMException('not expected', 'NotAllowedError');
        },
      },
    });
  });

  await page.goto('/login');
  await page.getByLabel(/e-mail/i).fill('contributor@example.test');
  await page.getByLabel(/mot de passe/i).fill('OpenSignDemo123!');
  await page.getByRole('button', { name: /se connecter/i }).click();
  await expect(page).toHaveURL(/\/app$/);

  await page.getByRole('link', { name: /contribuer/i }).click();
  await page.getByRole('link', { name: /gerer mes consentements/i }).click();
  await expect(page.getByText('Consentement dataset')).toBeVisible();
  await expect(page.getByRole('checkbox', { name: /LANDMARK PROCESSING/i })).not.toBeChecked();
  await expect(page.getByRole('checkbox', { name: /VIDEO RECORDING/i })).not.toBeChecked();
  await expect(page.getByRole('checkbox', { name: /PUBLIC DATASET RELEASE/i })).not.toBeChecked();
  const cameraRequested =
    (await page.evaluate(() => window.localStorage.getItem('camera-requested'))) === '1';
  expect(cameraRequested).toBe(false);
});
