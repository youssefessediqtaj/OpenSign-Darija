import { expect, test, type Page, type Request } from '@playwright/test';

const signs = [
  ['salam', 'سلام'],
  ['chokran', 'شكرا'],
  ['tabib', 'طبيب'],
  ['mosaada', 'مساعدة'],
  ['maa', 'ماء'],
].map(([key, label_ar]) => ({
  key,
  label_ar,
  darija_transliteration: key,
  reference_video_identifier: `opensigne-reference-${key}-v1`,
  reference_video_url: `/reference-signs/${key}.mp4`,
  poster_url: `/reference-signs/posters/${key}.svg`,
  reference_video_approved: true,
  recording_instructions: `Reproduisez une seule fois le signe « ${label_ar} ».`,
  active: true,
  expected_min_duration_seconds: 2,
  expected_max_duration_seconds: 10,
}));

const notice = {
  language: 'fr',
  arabic_translation_status: 'structure_ready_translation_pending',
  title: 'Notice d’information — contribution vidéo',
  summary:
    'Vos données servent uniquement à améliorer et évaluer la reconnaissance de la langue des signes marocaine.',
  controller_name: 'Contrôleur E2E isolé',
  controller_address: 'Adresse E2E',
  controller_contact: 'controller@example.test',
  purpose: 'améliorer et évaluer la reconnaissance de la langue des signes marocaine',
  collected_data: [
    { name: 'nom complet', required: true },
    { name: 'âge', required: true },
    { name: 'ville', required: true },
    { name: 'vidéo', required: true },
  ],
  refusal_consequence:
    'Aucune contribution ne sera envoyée, sans effet sur la reconnaissance normale.',
  recipient_categories: ['équipe modèle autorisée'],
  model_collaborator_sharing: 'Collaborateurs contractuellement autorisés uniquement.',
  storage_location_category: 'Stockage privé de test',
  retention_days: 30,
  rights: ['accès', 'rectification', 'opposition', 'retrait', 'suppression'],
  rights_request_method: 'rights@example.test',
  cndp_procedure_type: 'declaration',
  cndp_reference: 'E2E-TEST-ONLY',
  notice_version: 'e2e-notice-v1',
  consent_timestamp_source: 'Horodatage UTC généré par le serveur.',
  consent_checkbox_text:
    'J’ai lu la notice et j’accepte que mon nom, mon âge, ma ville et ma vidéo soient utilisés.',
  complete_notice: ['Aucun entraînement ni activation automatique.'],
};

async function installContributionCamera(page: Page) {
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
      context.fillRect(245 + Math.sin(frame / 8) * 25, 130, 150, 220);
      frame += 1;
    }, 33);
    const stream = canvas.captureStream(30);
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => stream,
        enumerateDevices: async () => [],
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      },
    });
  });
}

async function routeEnabledConfiguration(page: Page) {
  await page.route('**/api/v1/contributions/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        collection_enabled: true,
        compliance_configured: true,
        public_submission_allowed: true,
        collection_available: true,
        storage_status: 'available',
        message: 'La collecte des contributions est ouverte.',
        missing_configuration: [],
        invalid_configuration: [],
        readiness_dwell_ms: 800,
      }),
    });
  });
  await page.route('**/api/v1/contributions/signs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(signs),
    });
  });
  await page.route('**/api/v1/contributions/notice', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(notice),
    });
  });
  await page.route('**/reference-signs/*.mp4', async (route) => {
    await route.fulfill({ status: 204, body: '' });
  });
}

test('contribution remains fail-closed by default and transmits no personal data', async ({
  page,
}) => {
  const requests: Request[] = [];
  page.on('request', (request) => requests.push(request));
  await page.route('**/api/v1/contributions/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        collection_enabled: false,
        compliance_configured: false,
        public_submission_allowed: false,
        collection_available: false,
        storage_status: 'not_checked',
        message: 'La collecte des contributions n’est pas encore ouverte.',
        missing_configuration: ['CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE'],
        invalid_configuration: [],
        readiness_dwell_ms: 1000,
      }),
    });
  });
  await page.route('**/api/v1/contributions/signs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(
        signs.map((sign) => ({
          ...sign,
          reference_video_url: null,
          reference_video_approved: false,
        })),
      ),
    });
  });
  await page.route('**/api/v1/contributions/notice', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...notice, cndp_reference: '', notice_version: '' }),
    });
  });

  await page.goto('/contribute');
  await expect(page.getByText('La collecte des contributions n’est pas encore ouverte.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeDisabled();
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  expect(requests.filter((request) => request.method() === 'POST')).toHaveLength(0);
  expect(requests.some((request) => request.url().includes('Personne'))).toBe(false);
});

test('adult can explicitly record, retake and save once in an isolated enabled environment', async ({
  page,
}) => {
  test.setTimeout(30_000);
  await installContributionCamera(page);
  await routeEnabledConfiguration(page);
  const contributionPosts: Request[] = [];
  const forbiddenRequests: string[] = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('request', (request) => {
    const url = request.url();
    if (
      /\/predict|\/api\/v1\/speech|:8001\/|:8010\/|\/object|\/minio|analytics/i.test(url)
    ) {
      forbiddenRequests.push(url);
    }
  });
  await page.route('**/api/v1/contributions', async (route) => {
    contributionPosts.push(route.request());
    expect(route.request().headers()['content-type']).toContain('multipart/form-data');
    const body = route.request().postDataBuffer()?.toString('utf8') ?? '';
    expect(body).toContain('Personne E2E');
    expect(body).toContain('e2e-notice-v1');
    expect(body).toContain('salam');
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'received',
        contribution_id: '018fca31-87d8-7ae8-9000-000000000001',
        sign_key: 'salam',
        created_at: '2026-07-25T12:00:00Z',
        consent_notice_version: 'e2e-notice-v1',
        review_status: 'pending',
        deletion_request_instructions: 'Contactez rights@example.test.',
      }),
    });
  });

  await page.goto('/contribute?mockCamera=1');
  await expect(page.getByRole('heading', { name: 'سلام' })).toBeVisible();
  await expect(page.getByLabel('Vidéo officielle du signe سلام')).toHaveAttribute(
    'poster',
    '/reference-signs/posters/salam.svg',
  );
  await page.getByLabel('Nom complet', { exact: true }).fill('Personne E2E');
  await page.getByLabel('Âge', { exact: true }).fill('31');
  await page.getByLabel('Ville', { exact: true }).fill('Rabat');
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  expect(contributionPosts).toHaveLength(0);
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Activer la caméra' }).click();
  await expect(page.getByText('Prêt à enregistrer.')).toBeVisible({ timeout: 8_000 });

  await page.getByRole('button', { name: 'Enregistrer' }).click();
  await page.waitForTimeout(2200);
  await page.getByRole('button', { name: 'Arrêter' }).click();
  await expect(page.getByLabel('Aperçu de la contribution enregistrée')).toBeVisible();
  expect(contributionPosts).toHaveLength(0);
  await page.getByRole('button', { name: 'Recommencer' }).click();

  await page.getByRole('button', { name: 'Enregistrer' }).click();
  await page.waitForTimeout(2200);
  await page.getByRole('button', { name: 'Arrêter' }).click();
  await expect(page.getByLabel('Aperçu de la contribution enregistrée')).toBeVisible();
  expect(contributionPosts).toHaveLength(0);
  await page.getByRole('button', { name: 'Envoyer ma contribution' }).click();
  await expect(page.getByText('Contribution reçue')).toBeVisible();
  await expect(page.getByTestId('contribution-id')).toHaveText(
    '018fca31-87d8-7ae8-9000-000000000001',
  );
  expect(contributionPosts).toHaveLength(1);
  expect(contributionPosts[0].url()).not.toContain('Personne');
  expect(forbiddenRequests).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);

  await page.goto('/app/recognition');
  await expect(page.getByRole('heading', { name: 'Reconnaissance de signes' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeVisible();
});

test('Docker public gateway keeps contribution disabled by default', async ({ page, request }) => {
  const runtimeProcess = (globalThis as {
    process?: { env?: Record<string, string | undefined> };
  }).process;
  const dockerBaseUrl = runtimeProcess?.env?.DOCKER_E2E_BASE_URL ?? 'http://127.0.0.1:8081';
  let dockerAvailable = false;
  try {
    dockerAvailable = (await request.get(`${dockerBaseUrl}/api/v1/health`, { timeout: 2_000 })).ok();
  } catch {
    dockerAvailable = false;
  }
  test.skip(!dockerAvailable, `Docker stack unavailable at ${dockerBaseUrl}.`);
  await page.goto(`${dockerBaseUrl}/contribute`);
  await expect(page.getByText('La collecte des contributions n’est pas encore ouverte.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Activer la caméra' })).toBeDisabled();
});
