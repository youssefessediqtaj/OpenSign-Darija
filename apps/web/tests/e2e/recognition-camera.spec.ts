import { expect, test, type Page, type Request, type Response } from '@playwright/test';

function isBenignMediaPipeDiagnostic(message: string): boolean {
  return message === 'INFO: Created TensorFlow Lite XNNPACK delegate for CPU.';
}

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

test('one activation produces two automatic recognition and speech cycles', async ({ page }) => {
  await installCameraMock(page);
  const wordRequests: Request[] = [];
  const speechLabels: string[] = [];
  const forbiddenRequests: string[] = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('request', (request) => {
    if (/\/predict|recognitions\/alphabet|external-datasets|models\/active|\/auth\//.test(request.url())) {
      forbiddenRequests.push(request.url());
    }
  });

  await page.route('**/api/v1/recognitions/word', async (route) => {
    const request = route.request();
    expectPrivatePayload(request);
    wordRequests.push(request);
    const second = wordRequests.length === 2;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'recognized',
        label_key: second ? 'THANK_YOU' : 'HELLO',
        label_ar: second ? 'شكرا' : 'سلام',
        confidence: second ? 0.91 : 0.94,
        unknown: false,
        latency_ms: second ? 35 : 31,
      }),
    });
  });
  await page.route('**/api/v1/speech/sign', async (route) => {
    expect(route.request().headers()).not.toHaveProperty('authorization');
    const body = route.request().postDataJSON() as { label_key: string };
    speechLabels.push(body.label_key);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        generation_id: `speech-${speechLabels.length}`,
        status: 'ready',
        audio: { url: `/test-audio-${speechLabels.length}.wav`, mime_type: 'audio/wav' },
      }),
    });
  });

  await page.goto('/?mockCamera=1');
  const activation = page.getByRole('button', { name: 'Activer la caméra' });
  await activation.click();
  await expect(page.getByText('Caméra active')).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Prêt — Faites un signe');

  await expect(page.getByTestId('arabic-result')).toHaveText('سلام', { timeout: 10_000 });
  await expect(page.getByTestId('arabic-result')).toHaveText('شكرا', { timeout: 10_000 });
  await expect.poll(() => wordRequests.length, { timeout: 12_000 }).toBe(2);
  await expect.poll(() => speechLabels.length, { timeout: 12_000 }).toBe(2);

  expect(speechLabels).toEqual(['HELLO', 'THANK_YOU']);
  expect(forbiddenRequests).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  await page.waitForTimeout(1_500);
  expect(wordRequests).toHaveLength(2);
  expect(speechLabels).toHaveLength(2);
});

test('UNKNOWN displays text and never requests speech', async ({ page }) => {
  await installCameraMock(page);
  let speechRequests = 0;
  await page.route('**/api/v1/recognitions/word', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'unknown',
        label_key: null,
        label_ar: null,
        confidence: 0.28,
        unknown: true,
        latency_ms: 29,
      }),
    });
  });
  await page.route('**/api/v1/speech/sign', async (route) => {
    speechRequests += 1;
    await route.abort();
  });

  await page.goto('/?mockCamera=1');
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByTestId('arabic-result')).toHaveText('الإشارة غير معروفة', {
    timeout: 10_000,
  });
  expect(speechRequests).toBe(0);
});

test('real Docker API receives an automatic private sequence and returns its real compact decision', async ({
  page,
  request,
}) => {
  test.setTimeout(60_000);
  const runtimeProcess = (globalThis as {
    process?: { env?: Record<string, string | undefined> };
  }).process;
  const dockerBaseUrl = runtimeProcess?.env?.DOCKER_E2E_BASE_URL ?? 'http://127.0.0.1:8081';
  const fakeCameraVideo = runtimeProcess?.env?.PLAYWRIGHT_FAKE_CAMERA_VIDEO;
  const expectTwoSigns = runtimeProcess?.env?.PLAYWRIGHT_EXPECT_TWO_SIGNS === '1';
  let dockerAvailable = false;
  try {
    const health = await request.get(`${dockerBaseUrl}/api/v1/health`, { timeout: 2_000 });
    dockerAvailable = health.ok();
  } catch {
    dockerAvailable = false;
  }
  test.skip(
    !dockerAvailable,
    `Docker stack unavailable at ${dockerBaseUrl}; start it before the real API browser gate.`,
  );
  test.skip(
    !fakeCameraVideo,
    'Set PLAYWRIGHT_FAKE_CAMERA_VIDEO to a validated Y4M fixture for the real MediaPipe browser gate.',
  );

  const forbiddenRequests: string[] = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const speechRequests: Request[] = [];
  const wordResponses: Response[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' && !isBenignMediaPipeDiagnostic(message.text())) {
      consoleErrors.push(message.text());
    }
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('response', (browserResponse) => {
    if (
      browserResponse.url().includes('/api/v1/recognitions/word') &&
      browserResponse.request().method() === 'POST'
    ) {
      wordResponses.push(browserResponse);
    }
  });
  page.on('request', (browserRequest) => {
    const url = browserRequest.url();
    if (
      /\/predict|recognitions\/alphabet|external-datasets|dataset-import|kaggle|mendeley|sciencedirect/i.test(
        url,
      )
    ) {
      forbiddenRequests.push(url);
    }
    if (url.includes('/api/v1/speech/sign')) speechRequests.push(browserRequest);
  });

  await page.goto(`${dockerBaseUrl}/app/recognition`);
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByRole('status')).toContainText('Prêt — Faites un signe', {
    timeout: 20_000,
  });

  if (expectTwoSigns) {
    await expect.poll(() => wordResponses.length, { timeout: 25_000 }).toBe(2);
  } else {
    await expect.poll(() => wordResponses.length, { timeout: 25_000 }).toBeGreaterThanOrEqual(1);
  }
  if (!expectTwoSigns && wordResponses.length === 1) {
    await page
      .waitForResponse(
        (response) =>
          response.url().includes('/api/v1/recognitions/word') &&
          response.request().method() === 'POST',
        { timeout: 8_000 },
      )
      .catch(() => null);
  }

  expect(wordResponses.length).toBeLessThanOrEqual(2);
  if (expectTwoSigns) expect(wordResponses).toHaveLength(2);

  type CompactDecision = {
    status: 'recognized' | 'unknown';
    label_key: string | null;
    label_ar: string | null;
    confidence: number;
    unknown: boolean;
    latency_ms: number;
  };
  const decisions: CompactDecision[] = [];
  for (const response of wordResponses) {
    expect(response.status()).toBe(200);
    expectPrivatePayload(response.request());
    const decision = (await response.json()) as CompactDecision;
    expect(Object.keys(decision).sort()).toEqual(
      ['status', 'label_key', 'label_ar', 'confidence', 'unknown', 'latency_ms'].sort(),
    );
    expect(decision.confidence).toBeGreaterThanOrEqual(0);
    expect(decision.confidence).toBeLessThanOrEqual(1);
    expect(decision.latency_ms).toBeGreaterThanOrEqual(0);
    if (decision.status === 'recognized') {
      expect(decision.unknown).toBe(false);
      expect(decision.label_key).toEqual(expect.any(String));
      expect(decision.label_ar).toEqual(expect.any(String));
    } else {
      expect(decision).toMatchObject({
        unknown: true,
        label_key: null,
        label_ar: null,
      });
    }
    decisions.push(decision);
  }

  const expectedSpeechLabels = decisions.flatMap((decision) =>
    decision.status === 'recognized' && decision.label_key ? [decision.label_key] : [],
  );
  const captureCadences = wordResponses.map(
    (response) =>
      (response.request().postDataJSON() as { source_fps: number }).source_fps,
  );
  if (expectTwoSigns) {
    expect(decisions.every((decision) => decision.status === 'recognized')).toBe(true);
    expect(captureCadences).toHaveLength(2);
    captureCadences.forEach((sourceFps) => expect(sourceFps).toBeGreaterThanOrEqual(15));
  }
  if (expectedSpeechLabels.length > 0) {
    await expect.poll(() => speechRequests.length, { timeout: 8_000 }).toBe(expectedSpeechLabels.length);
  }
  const observedSpeechLabels = speechRequests.map(
    (speechRequest) => (speechRequest.postDataJSON() as { label_key: string }).label_key,
  );
  expect(observedSpeechLabels).toEqual(expectedSpeechLabels);
  for (const speechRequest of speechRequests) {
    expect(speechRequest.headers()).not.toHaveProperty('authorization');
  }

  const finalDecision = decisions[decisions.length - 1];
  if (finalDecision?.status === 'recognized') {
    await expect(page.getByTestId('arabic-result')).toHaveText(finalDecision.label_ar ?? '', {
      timeout: 5_000,
    });
  } else {
    await expect(page.getByTestId('arabic-result')).toHaveText('الإشارة غير معروفة', {
      timeout: 5_000,
    });
  }

  await expect(page.getByRole('status')).toContainText('Prêt — Faites un signe', {
    timeout: 25_000,
  });
  const completedResponseCount = wordResponses.length;
  await page.waitForTimeout(2_000);
  expect(wordResponses).toHaveLength(completedResponseCount);
  expect(wordResponses.length).toBeLessThanOrEqual(2);
  if (expectTwoSigns) expect(wordResponses).toHaveLength(2);
  expect(speechRequests).toHaveLength(expectedSpeechLabels.length);
  expect(forbiddenRequests).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
});
