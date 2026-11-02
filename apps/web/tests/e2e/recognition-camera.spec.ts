import { expect, test, type Page, type Request } from '@playwright/test';

async function installCameraMock(page: Page) {
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
    const testWindow = window as unknown as { __cameraRequests: number };
    testWindow.__cameraRequests = 0;
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => { testWindow.__cameraRequests += 1; return stream; },
        enumerateDevices: async () => [
          { kind: 'videoinput', deviceId: 'front', label: 'Front camera', groupId: 'test' },
        ],
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      },
    });

    const nativeLoad = HTMLMediaElement.prototype.load;
    const nativePlay = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.load = function load() {
      if (this instanceof HTMLAudioElement) return;
      nativeLoad.call(this);
    };
    HTMLMediaElement.prototype.play = function play() {
      if (this instanceof HTMLAudioElement) {
        window.setTimeout(() => this.dispatchEvent(new Event('ended')), 250);
        return Promise.resolve();
      }
      return nativePlay.call(this);
    };
  });
}

function expectPrivatePayload(request: Request) {
  const payload = request.postDataJSON() as Record<string, unknown>;
  expect(request.headers()).not.toHaveProperty('authorization');
  expect(payload).toMatchObject({
    recognition_mode: 'WORD_ISOLATED',
    target_frame_count: 60,
    landmark_count: 75,
    coordinate_count: 3,
    coordinate_format: 'shoulder_centered_v1',
    feature_schema_version: 'OPEN_SIGNE_LANDMARK_SCHEMA_V1',
    segmentation_reliable: true,
    usable_frame_count: expect.any(Number),
  });
  expect(['dynamic', 'static']).toContain(payload.segmentation_kind);
  expect(payload.usable_frame_count).toEqual(expect.any(Number));
  expect(payload.usable_frame_count as number).toBeGreaterThanOrEqual(8);
  expect(payload.usable_frame_count as number).toBeLessThanOrEqual(60);
  expect(payload).not.toHaveProperty('anonymous_session_id');
  expect(payload).not.toHaveProperty('video');
  expect(payload).not.toHaveProperty('image');
  expect(payload).not.toHaveProperty('audio');
  expect(JSON.stringify(payload)).not.toContain('base64');

  const frames = payload.frames as Array<{
    landmarks: number[][];
    presence_mask: number[];
    timestamp_ms: number;
  }>;
  expect(frames).toHaveLength(60);
  for (const [index, frame] of frames.entries()) {
    expect(frame.landmarks).toHaveLength(75);
    expect(frame.presence_mask).toHaveLength(75);
    expect(frame.timestamp_ms).toBeGreaterThanOrEqual(0);
    expect(frame.timestamp_ms).toBeLessThanOrEqual(10_000);
    if (index > 0) expect(frame.timestamp_ms).toBeGreaterThan(frames[index - 1].timestamp_ms);
    expect(frame.landmarks.every((landmark) => landmark.length === 3)).toBe(true);
    expect(frame.landmarks.flat().every(Number.isFinite)).toBe(true);
  }
}

test('root and compatibility URL expose only the public recognition product', async ({ page }) => {
  for (const path of ['/', '/app/recognition']) {
    await page.goto(path);
    await expect(page.getByText('OpenSigne Darija', { exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Reconnaissance de signes' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeVisible();
    await expect(page.getByText(/connexion|alphabet|contribuer|messages|paramètres|admin/i)).toHaveCount(0);
  }
});

test('camera permission refusal remains understandable', async ({ page }) => {
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
  await page.goto('/');
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByText(/accès à la caméra a été refusé/i)).toBeVisible();
});

test('color candidates and Sign Again preserve the camera and never request legacy or speech', async ({ page }) => {
  await installCameraMock(page);
  let requests = 0;
  const forbidden: string[] = [];
  page.on('request', (request) => {
    if (/recognitions\/word|speech\/sign/.test(request.url())) forbidden.push(request.url());
  });
  await page.route('**/api/v1/recognitions/colors-experimental?*', async (route) => {
    expectPrivatePayload(route.request());
    requests += 1;
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      model_id: 'colors_v1_gru_experimental', recognition_state: 'UNKNOWN_SIGN',
      candidate: requests === 1 ? 'blue' : 'red', raw_score: null,
      calibration_status: 'UNCALIBRATED', experimental: true,
    }) });
  });
  await page.goto('/?mockCamera=1');
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByText('🔵 Bleu — Prédiction expérimentale')).toBeVisible({ timeout: 12_000 });
  await page.evaluate(() => {
    (window as unknown as { __originalStream: MediaProvider | null }).__originalStream = document.querySelector('video')?.srcObject ?? null;
  });
  await page.getByRole('button', { name: 'Refaire un signe' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('🔵 Bleu — Prédiction expérimentale')).toHaveCount(0);
  expect(await page.evaluate(() => {
    const state = window as unknown as { __originalStream: MediaProvider | null; __cameraRequests: number };
    return Boolean(state.__originalStream) && document.querySelector('video')?.srcObject === state.__originalStream && state.__cameraRequests === 1;
  })).toBe(true);
  await expect(page.getByText('🔴 Rouge — Prédiction expérimentale')).toBeVisible({ timeout: 12_000 });
  expect(requests).toBe(2);
  expect(forbidden).toEqual([]);
});

test('model unavailable is distinct from an unknown sign', async ({ page }) => {
  await installCameraMock(page);
  await page.route('**/api/v1/recognitions/colors-experimental?*', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      model_id: 'colors_v1_gru_experimental', recognition_state: 'MODEL_NOT_READY', candidate: null,
      raw_score: null, calibration_status: 'UNCALIBRATED', experimental: true,
    }) });
  });
  await page.goto('/?mockCamera=1');
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByText(/MODEL_NOT_READY/)).toBeVisible({ timeout: 12_000 });
  await expect(page.getByText(/Couleur détectée/)).toHaveCount(0);
});

test('real Docker camera processes colors when a validated fake video is supplied', async ({ page, request }) => {
  test.setTimeout(60_000);
  const runtime = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process;
  const base = runtime?.env?.DOCKER_E2E_BASE_URL ?? 'http://127.0.0.1:8081';
  const video = runtime?.env?.PLAYWRIGHT_FAKE_CAMERA_VIDEO;
  let available = false;
  try { available = (await request.get(`${base}/api/v1/health`, { timeout: 2_000 })).ok(); } catch { /* unavailable */ }
  test.skip(!available || !video, 'Requires the local Docker stack and PLAYWRIGHT_FAKE_CAMERA_VIDEO.');
  const forbidden: string[] = [];
  page.on('request', (r) => { if (/recognitions\/word|speech\/sign/.test(r.url())) forbidden.push(r.url()); });
  await page.goto(`${base}/app/recognition`);
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  const response = await page.waitForResponse((r) => r.url().includes('/recognitions/colors-experimental') && r.request().method() === 'POST', { timeout: 30_000 });
  expect(response.status()).toBe(200);
  expectPrivatePayload(response.request());
  expect(await response.json()).toMatchObject({ model_id: 'colors_v1_gru_experimental', experimental: true, calibration_status: 'UNCALIBRATED' });
  expect(forbidden).toEqual([]);
});

test('local diagnostics capture raw ranking without media or landmarks', async ({ page }) => {
  await installCameraMock(page);
  await page.route('**/api/v1/recognitions/colors-experimental?*', async (route) => {
    expect(route.request().url()).toContain('trace=true');
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      model_id: 'colors_v1_gru_experimental', model_version: '0.1.0-smoke',
      recognition_state: 'UNKNOWN_SIGN', candidate: 'green', raw_score: 0.4,
      calibration_status: 'UNCALIBRATED', experimental: true,
      diagnostics: { feature_schema_version: 'COLORS_V1_VIDEO_V1_EXPERIMENTAL', output_shape: [1, 9],
        top_three: [{ label: 'green', raw_score: 0.4 }, { label: 'red', raw_score: 0.2 }, { label: 'pink', raw_score: 0.1 }] },
    }) });
  });
  await page.goto('/?mockCamera=1&diagnostics=1');
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByText('🟢 Vert — Prédiction expérimentale')).toBeVisible({ timeout: 12_000 });
  await page.getByText(/Diagnostics locaux/).click();
  const records = JSON.parse(await page.getByTestId('attempt-diagnostics').innerText());
  expect(records).toHaveLength(1);
  expect(records[0]).toMatchObject({ completion_reason: 'stable', request_status: 'response_received',
    sequence_length: 60, output_shape: [1, 9], model_version: '0.1.0-smoke' });
  expect(records[0].top_three_raw_scores).toHaveLength(3);
  expect(JSON.stringify(records)).not.toMatch(/landmarks|presence_mask|data:image/);
});
