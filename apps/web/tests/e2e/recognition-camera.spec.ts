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

async function routeActiveModels(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/models/active**', async (route) => {
    const url = route.request().url();
    const isAlphabet = url.includes('ALPHABET_STATIC');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: isAlphabet ? 'alphabet-model-1' : 'word-model-1',
        model_name: isAlphabet ? 'alphabet-smoke' : 'mosl-word-smoke-v1',
        model_version: '0.1.0-smoke',
        task_type: isAlphabet ? 'ALPHABET_STATIC' : 'WORD_ISOLATED',
        is_active: true,
        status: 'VALIDATED_SMOKE',
        supported_classes: isAlphabet ? ['ARABIC_LETTER_ALEF'] : ['16', '17'],
      }),
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

test('mock camera submits a WORD_ISOLATED V1 landmark payload', async ({ page }) => {
  await installCameraMock(page);
  await routeActiveModels(page);
  await page.route('**/api/v1/recognitions/word', async (route) => {
    const body = route.request().postDataJSON();
    expect(route.request().method()).toBe('POST');
    expect(body).toMatchObject({
      recognition_mode: 'WORD_ISOLATED',
      target_frame_count: 60,
      landmark_count: 75,
      coordinate_count: 3,
      coordinate_format: 'shoulder_centered_v1',
      feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1',
    });
    expect(body.frames).toHaveLength(60);
    expect(body.frames[0].landmarks).toHaveLength(75);
    expect(body.frames[0].landmarks[0]).toHaveLength(3);
    expect(body.frames[0].presence_mask).toHaveLength(75);
    expect(body).not.toHaveProperty('video');
    expect(body).not.toHaveProperty('image');
    expect(body).not.toHaveProperty('audio');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        recognition_id: 'rec-1',
        request_id: 'req-1',
        sequence_id: 'seq-1',
        status: 'completed',
        model_name: 'mosl-word-smoke-v1',
        model_version: '0.1.0-smoke',
        feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1',
        predictions: [
          { prediction_id: 'pred-1', label: '16', confidence: 0.79, rank: 1 },
          { prediction_id: 'pred-2', label: '17', confidence: 0.16, rank: 2 },
        ],
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

test('alphabet mode submits only the compact alphabet request', async ({ page }) => {
  await installCameraMock(page);
  await routeActiveModels(page);
  await page.route('**/api/v1/recognitions/alphabet', async (route) => {
    const body = route.request().postDataJSON();
    expect(route.request().method()).toBe('POST');
    expect(body).toMatchObject({
      feature_schema_version: '1.0.0',
      stability_frames: expect.any(Number),
    });
    expect(body.features).toHaveLength(63);
    expect(body.presence_mask).toHaveLength(21);
    expect(body).not.toHaveProperty('frames');
    expect(body).not.toHaveProperty('video');
    expect(body).not.toHaveProperty('image');
    expect(body).not.toHaveProperty('audio');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        recognition_id: 'rec-alpha-1',
        request_id: 'req-alpha-1',
        sequence_id: body.sequence_id,
        status: 'completed',
        model_name: 'alphabet-smoke',
        model_version: '0.1.0-smoke',
        feature_schema_version: '1.0.0',
        predictions: [
          {
            prediction_id: 'pred-alpha-1',
            label: 'ARABIC_LETTER_ALEF',
            confidence: 0.88,
            rank: 1,
          },
        ],
        unknown_probability: 0.02,
        processing_time_ms: 18,
      }),
    });
  });
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('tab', { name: /Epeler|Épeler/i }).click();
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await expect(page.getByText(/Camera active/i)).toBeVisible();
  await page.waitForTimeout(300);
  await page.getByRole('button', { name: /Analyser la lettre stable/i }).click();
  await expect(page.getByText(/Confiance 88%/i)).toBeVisible();
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
  await routeActiveModels(page);
  await page.route('**/api/v1/recognitions/word', async (route) => route.abort());
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await page.getByRole('button', { name: /^Commencer$/i }).click();
  await expect(page.getByRole('button', { name: /Terminer/i })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(900);
  await page.getByRole('button', { name: /Terminer/i }).click();
  await expect(page.getByText(/backend est indisponible/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /Desactiver la camera/i })).toBeEnabled();
});

test('mock camera word capture reaches the real Docker API with V1 payload', async ({ page }) => {
  await installCameraMock(page);
  await routeActiveModels(page);
  const directInferenceRequests: string[] = [];
  page.on('request', (request) => {
    const url = request.url();
    if (url.includes('/predict')) directInferenceRequests.push(url);
  });
  const wordResponsePromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/recognitions/word') && response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  let inspectedPayload: Record<string, unknown> | undefined;
  page.on('request', (request) => {
    if (request.url().includes('/api/v1/recognitions/word') && request.method() === 'POST') {
      inspectedPayload = request.postDataJSON() as Record<string, unknown>;
    }
  });
  await page.goto('/app/recognition?mockCamera=1');
  await page.getByRole('button', { name: /Activer la camera/i }).first().click();
  await expect(page.getByText(/Camera active/i)).toBeVisible();
  await page.getByRole('button', { name: /^Commencer$/i }).click();
  await expect(page.getByRole('button', { name: /Terminer/i })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(900);
  await page.getByRole('button', { name: /Terminer/i }).click();
  const response = await wordResponsePromise;
  expect(response.status()).not.toBe(422);
  expect(response.status()).toBe(200);
  if (!inspectedPayload) throw new Error('WORD_ISOLATED request payload was not captured');
  const payload = inspectedPayload;
  expect(payload).toMatchObject({
    sequence_id: expect.stringMatching(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    ),
    recognition_mode: 'WORD_ISOLATED',
    feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1',
    target_frame_count: 60,
    landmark_count: 75,
    coordinate_count: 3,
  });
  const frames = payload.frames as Array<{
    landmarks: number[][];
    presence_mask: number[];
    timestamp_ms: number;
  }>;
  expect(frames).toHaveLength(60);
  for (const frame of frames) {
    expect(frame.timestamp_ms).toBeGreaterThanOrEqual(0);
    expect(frame.timestamp_ms).toBeLessThanOrEqual(10_000);
    expect(frame.landmarks).toHaveLength(75);
    expect(frame.presence_mask).toHaveLength(75);
    for (const landmark of frame.landmarks) {
      expect(landmark).toHaveLength(3);
      expect(landmark.every(Number.isFinite)).toBe(true);
    }
  }
  expect(payload).not.toHaveProperty('video');
  expect(payload).not.toHaveProperty('image');
  expect(JSON.stringify(payload)).not.toContain('base64');
  expect(payload).not.toHaveProperty('audio');
  expect(directInferenceRequests).toEqual([]);
  await expect(
    page.getByText('Reconnaissance expérimentale d’un vocabulaire limité.', { exact: true }),
  ).toBeVisible();
});
