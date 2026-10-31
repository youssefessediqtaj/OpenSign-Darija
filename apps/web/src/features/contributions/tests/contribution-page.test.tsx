import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ContributionPage } from '../components/ContributionPage';
import { INITIAL_READINESS } from '../domain/readiness-policy';
import { useContributionCamera } from '../hooks/useContributionCamera';
import { useContributionRecording } from '../hooks/useContributionRecording';
import type {
  ContributionNotice,
  ContributionSign,
  ContributionStatus,
} from '../types';

vi.mock('../hooks/useContributionCamera', () => ({ useContributionCamera: vi.fn() }));
vi.mock('../hooks/useContributionRecording', () => ({ useContributionRecording: vi.fn() }));

const signs: ContributionSign[] = [
  ['salam', 'سلام'],
  ['chokran', 'شكرا'],
  ['tabib', 'طبيب'],
  ['mosaada', 'مساعدة'],
  ['maa', 'ماء'],
].map(([key, label_ar]) => ({
  key: key as ContributionSign['key'],
  label_ar,
  darija_transliteration: key,
  reference_video_identifier: `reference-${key}`,
  reference_video_url: `/reference-signs/${key}.mp4`,
  poster_url: `/reference-signs/posters/${key}.svg`,
  reference_video_approved: true,
  recording_instructions: `Instruction ${label_ar}`,
  active: true,
  expected_min_duration_seconds: 2,
  expected_max_duration_seconds: 10,
}));

const notice: ContributionNotice = {
  language: 'fr',
  arabic_translation_status: 'structure_ready_translation_pending',
  title: 'Notice d’information — contribution vidéo',
  summary: 'Résumé clair.',
  controller_name: 'Responsable Test',
  controller_address: 'Adresse Test',
  controller_contact: 'controller@example.test',
  purpose: 'améliorer et évaluer la reconnaissance de la langue des signes marocaine',
  collected_data: [{ name: 'nom complet', required: true }],
  refusal_consequence: 'Aucune contribution ne sera envoyée.',
  recipient_categories: ['équipe modèle'],
  model_collaborator_sharing: 'Collaborateurs autorisés.',
  storage_location_category: 'Stockage privé',
  retention_days: 30,
  rights: ['accès', 'rectification', 'opposition'],
  rights_request_method: 'rights@example.test',
  cndp_procedure_type: 'declaration',
  cndp_reference: 'TEST-REFERENCE',
  notice_version: 'notice-v1',
  consent_timestamp_source: 'Horodatage serveur.',
  consent_checkbox_text:
    'J’ai lu la notice et j’accepte que mon nom, mon âge, ma ville et ma vidéo soient utilisés.',
  complete_notice: ['Aucune activation automatique de modèle.'],
};

const openStatus: ContributionStatus = {
  collection_enabled: true,
  compliance_configured: true,
  public_submission_allowed: true,
  collection_available: true,
  storage_status: 'available',
  message: 'La collecte des contributions est ouverte.',
  missing_configuration: [],
  invalid_configuration: [],
  readiness_dwell_ms: 1000,
};

const closedStatus: ContributionStatus = {
  ...openStatus,
  collection_enabled: false,
  public_submission_allowed: false,
  collection_available: false,
  storage_status: 'not_checked',
  message: 'La collecte des contributions n’est pas encore ouverte.',
};

const fakeStream = { getTracks: () => [] } as unknown as MediaStream;
const cameraActivate = vi.fn();
const cameraStop = vi.fn();
const recordingStart = vi.fn();
const recordingStop = vi.fn();
const recordingDiscard = vi.fn();

function mockCamera(active = false, ready = false) {
  vi.mocked(useContributionCamera).mockReturnValue({
    stream: active ? fakeStream : null,
    cameraActive: active,
    detectorStatus: active ? 'ready' : 'idle',
    readiness: {
      ...INITIAL_READINESS,
      detectorReady: active,
      faceVisible: ready,
      leftHandVisible: ready,
      upperBodyFramed: ready,
      adequateLighting: ready,
      acceptableDistance: ready,
      stable: ready,
      rawReady: ready,
      dwellReady: ready,
      guidance: ready ? 'Prêt à enregistrer.' : 'Gardez au moins une main visible.',
    },
    error: null,
    activate: cameraActivate,
    stop: cameraStop,
  });
}

function mockRecording(withPreview = false) {
  vi.mocked(useContributionRecording).mockReturnValue({
    isRecording: false,
    elapsedSeconds: withPreview ? 3 : 0,
    preview: withPreview
      ? {
          blob: new Blob(['video'], { type: 'video/webm' }),
          url: 'blob:preview',
          durationSeconds: 3,
          mimeType: 'video/webm',
        }
      : null,
    error: null,
    start: recordingStart,
    stop: recordingStop,
    discard: recordingDiscard,
  });
}

function installApi(status: ContributionStatus, receipt = false) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input);
    if (init?.method === 'POST') {
      expect(receipt).toBe(true);
      return new Response(
        JSON.stringify({
          status: 'received',
          contribution_id: '018fca31-87d8-7ae8-9000-000000000001',
          sign_key: 'salam',
          created_at: '2026-07-25T12:00:00Z',
          consent_notice_version: 'notice-v1',
          review_status: 'pending',
          deletion_request_instructions: 'Contactez rights@example.test.',
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      );
    }
    const payload = url.endsWith('/status') ? status : url.endsWith('/signs') ? signs : notice;
    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ContributionPage />
    </MemoryRouter>,
  );
}

async function completeAdultForm() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Nom complet'), 'Personne Test');
  await user.type(screen.getByLabelText('Âge'), '29');
  await user.type(screen.getByLabelText('Ville'), 'Rabat');
  await user.click(screen.getByRole('checkbox'));
  return user;
}

describe('ContributionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCamera();
    mockRecording();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows exactly five server-controlled signs and fail-closed preview without PII transmission', async () => {
    const fetch = installApi(closedStatus);
    renderPage();
    await screen.findByText('La collecte des contributions n’est pas encore ouverte.');
    expect(screen.getAllByRole('radio')).toHaveLength(5);
    expect(screen.getAllByText('سلام')).toHaveLength(2);
    expect(screen.getByText('شكرا')).toBeVisible();
    expect(screen.getByText('طبيب')).toBeVisible();
    expect(screen.getByText('مساعدة')).toBeVisible();
    expect(screen.getByText('ماء')).toBeVisible();
    expect(screen.getByRole('checkbox')).not.toBeChecked();
    expect(screen.getByRole('checkbox')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Activer la caméra' })).toBeDisabled();
    expect(cameraActivate).not.toHaveBeenCalled();
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls.every((call) => !String(call[1]?.body ?? '').includes('Personne'))).toBe(
      true,
    );
  });

  it('requires the adult form and unchecked-by-default explicit consent before camera activation', async () => {
    installApi(openStatus);
    renderPage();
    await screen.findByText('La collecte des contributions est ouverte.');
    const activate = screen.getByRole('button', { name: 'Activer la caméra' });
    expect(screen.getByRole('checkbox')).not.toBeChecked();
    expect(activate).toBeDisabled();
    const user = await completeAdultForm();
    expect(activate).toBeEnabled();
    expect(cameraActivate).not.toHaveBeenCalled();
    await user.click(activate);
    expect(cameraActivate).toHaveBeenCalledTimes(1);
  });

  it('blocks underage recording without submitting data', async () => {
    const fetch = installApi(openStatus);
    renderPage();
    await screen.findByText('La collecte des contributions est ouverte.');
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Nom complet'), 'Personne Mineure');
    await user.type(screen.getByLabelText('Âge'), '17');
    await user.type(screen.getByLabelText('Ville'), 'Rabat');
    expect(screen.getByText(/réservé aux adultes/i)).toBeVisible();
    expect(screen.getByRole('checkbox')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Activer la caméra' })).toBeDisabled();
    expect(fetch.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(0);
  });

  it('keeps record disabled before readiness and starts only after an explicit click', async () => {
    installApi(openStatus);
    mockCamera(true, false);
    const view = renderPage();
    await screen.findByText('La collecte des contributions est ouverte.');
    await completeAdultForm();
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeDisabled();
    expect(recordingStart).not.toHaveBeenCalled();

    mockCamera(true, true);
    act(() =>
      view.rerender(
        <MemoryRouter>
          <ContributionPage />
        </MemoryRouter>,
      ),
    );
    const record = screen.getByRole('button', { name: 'Enregistrer' });
    await waitFor(() => expect(record).toBeEnabled());
    await userEvent.click(record);
    expect(recordingStart).toHaveBeenCalledWith(fakeStream);
  });

  it('retakes locally and submits one multipart request only after save', async () => {
    const fetch = installApi(openStatus, true);
    mockCamera(true, true);
    mockRecording(true);
    renderPage();
    await screen.findByText('La collecte des contributions est ouverte.');
    const user = await completeAdultForm();
    expect(screen.getByLabelText('Vidéo officielle du signe سلام')).toBeVisible();
    expect(screen.getByLabelText('Caméra du contributeur')).toBeVisible();
    expect(screen.getByLabelText('Aperçu de la contribution enregistrée')).toBeVisible();
    expect(fetch.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(0);

    await user.click(screen.getByRole('button', { name: 'Recommencer' }));
    expect(recordingDiscard).toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Envoyer ma contribution' }));
    await screen.findByText('Contribution reçue');
    const posts = fetch.mock.calls.filter((call) => call[1]?.method === 'POST');
    expect(posts).toHaveLength(1);
    const body = posts[0][1]?.body;
    expect(body).toBeInstanceOf(FormData);
    const form = body as FormData;
    expect(form.get('full_name')).toBe('Personne Test');
    expect(form.get('sign_key')).toBe('salam');
    expect(form.get('consent_accepted')).toBe('true');
    expect(form.get('consent_notice_version')).toBe('notice-v1');
    expect(form.get('video')).toBeInstanceOf(Blob);
    expect(screen.queryByText(/storage|objet/i)).not.toBeInTheDocument();
  });
});
