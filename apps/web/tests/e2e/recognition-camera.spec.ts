import { expect, test } from '@playwright/test';

async function installCameraMock(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const context = canvas.getContext('2d');
    let frame = 0;
    window.setInterval(() => {
      if (!context) return;
      context.fillStyle = '#f8fafc';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = '#0f766e';
      context.fillRect(260 + Math.sin(frame / 10) * 30, 160, 120, 160);
      frame += 1;
    }, 33);
    const stream = canvas.captureStream(30);
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => stream,
        enumerateDevices: async () => [
          { kind: 'videoinput', deviceId: 'front', label: 'Front camera', groupId: 'test' },
        ],
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      },
    });
  });
}

test('user refuses the camera', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => {
          throw new DOMException('denied', 'NotAllowedError');
        },
        enumerateDevices: async () => [],
      },
    });
  });
  await page.goto('/app/recognition');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await expect(page.getByText(/refuse/i)).toBeVisible();
});

test('no camera available shows a clear error', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => {
          throw new DOMException('missing', 'NotFoundError');
        },
        enumerateDevices: async () => [],
      },
    });
  });
  await page.goto('/app/recognition');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await expect(page.getByText(/Aucune camera compatible/i)).toBeVisible();
});

test('mock camera can capture and render a simulated result', async ({ page }) => {
  await installCameraMock(page);
  await page.route('**/api/v1/recognitions', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        recognition_id: 'rec-1',
        request_id: 'req-1',
        sequence_id: 'seq-1',
        status: 'completed',
        model_name: 'opensign-darija-landmark-mock',
        model_version: '0.2.0',
        feature_schema_version: '1.0.0',
        predictions: [{ prediction_id: 'pred-1', label: 'aide', confidence: 0.79, rank: 1 }],
        unknown_probability: 0.03,
        processing_time_ms: 42,
      }),
    });
  });
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await expect(page.getByText(/Camera active/i)).toBeVisible();
  await expect(page.getByText(/Vous etes correctement positionne/i)).toBeVisible();
  await page.getByRole('button', { name: /^Commencer$/i }).click();
  await expect(page.getByRole('button', { name: /Terminer/i })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(900);
  await page.getByRole('button', { name: /Terminer/i }).click();
  await expect(
    page.getByText('Reconnaissance expérimentale d’un vocabulaire limité.', { exact: true }),
  ).toBeVisible();
});

test('too short sequence is rejected locally', async ({ page }) => {
  await installCameraMock(page);
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await page.getByRole('button', { name: /^Commencer$/i }).click();
  await expect(page.getByRole('button', { name: /Terminer/i })).toBeVisible({ timeout: 5000 });
  await page.getByRole('button', { name: /Terminer/i }).click();
  await expect(page.getByText(/sequence_too_short|trop courte|insufficient/i)).toBeVisible();
});

test('backend unavailable keeps camera controllable', async ({ page }) => {
  await installCameraMock(page);
  await page.route('**/api/v1/recognitions', async (route) => route.abort());
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await page.getByRole('button', { name: /^Commencer$/i }).click();
  await expect(page.getByRole('button', { name: /Terminer/i })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(900);
  await page.getByRole('button', { name: /Terminer/i }).click();
  await expect(page.getByText(/backend est indisponible/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /Desactiver la camera/i })).toBeEnabled();
});
