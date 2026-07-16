import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { DemoPage } from './DemoPage';
import { renderWithProviders } from '../test/render';

describe('DemoPage', () => {
  it('shows a simulated recognition result', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            request_id: 'request-1',
            status: 'completed',
            model_name: 'opensign-darija-mock',
            model_version: '0.1.0',
            predictions: [{ label: 'medecin', confidence: 0.82, rank: 1 }],
            unknown_probability: 0.03,
            processing_time_ms: 12,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    renderWithProviders(<DemoPage />);
    await userEvent.click(screen.getByRole('button', { name: /Autoriser la camera/i }));
    await userEvent.click(screen.getByRole('button', { name: /Demarrer/i }));
    expect(await screen.findByText(/medecin/i)).toBeInTheDocument();
  });
});
