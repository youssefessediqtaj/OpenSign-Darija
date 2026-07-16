import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ConsentPage } from './ContributionPages';
import { renderWithProviders } from '../test/render';

const template = {
  id: 'template-1',
  code: 'dataset-collection',
  version: '1.0.0',
  language: 'fr',
  title: 'Consentement dataset',
  summary: 'Choix separes',
  full_text: 'Texte complet',
  is_active: true,
};

describe('ConsentPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('keeps consent boxes unchecked and submits separate choices', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/v1/consents/templates')) {
        return Response.json([template]);
      }
      if (url.endsWith('/api/v1/consents/me')) {
        return Response.json([]);
      }
      if (url.endsWith('/api/v1/consents') && init?.method === 'POST') {
        return Response.json([]);
      }
      return new Response('', { status: 404 });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithProviders(<ConsentPage />);

    expect(await screen.findByText('Consentement dataset')).toBeInTheDocument();
    const landmarkProcessing = screen.getByRole('checkbox', { name: /LANDMARK PROCESSING/i });
    const videoRecording = screen.getByRole('checkbox', { name: /VIDEO RECORDING/i });
    const publicRelease = screen.getByRole('checkbox', { name: /PUBLIC DATASET RELEASE/i });
    expect(landmarkProcessing).not.toBeChecked();
    expect(videoRecording).not.toBeChecked();
    expect(publicRelease).not.toBeChecked();

    await userEvent.click(landmarkProcessing);
    await userEvent.click(screen.getByRole('checkbox', { name: /LANDMARK STORAGE/i }));
    await userEvent.click(screen.getByRole('checkbox', { name: /RESEARCH USE/i }));
    await userEvent.click(screen.getByRole('checkbox', { name: /MODEL TRAINING/i }));
    await userEvent.click(screen.getByRole('button', { name: /enregistrer mes choix/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/consents',
        expect.objectContaining({ method: 'POST' }),
      );
    });
    const createCall = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith('/api/v1/consents') && init?.method === 'POST',
    );
    const body = JSON.parse(String(createCall?.[1]?.body));
    expect(body.choices).toEqual(
      expect.arrayContaining([
        { consent_type: 'LANDMARK_PROCESSING', granted: true },
        { consent_type: 'LANDMARK_STORAGE', granted: true },
        { consent_type: 'RESEARCH_USE', granted: true },
        { consent_type: 'MODEL_TRAINING', granted: true },
        { consent_type: 'VIDEO_RECORDING', granted: false },
        { consent_type: 'VIDEO_STORAGE', granted: false },
        { consent_type: 'PUBLIC_DATASET_RELEASE', granted: false },
      ]),
    );
  });
});
