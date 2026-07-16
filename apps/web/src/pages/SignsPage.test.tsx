import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SignsPage } from './SignsPage';
import { renderWithProviders } from '../test/render';

describe('SignsPage', () => {
  it('renders the fallback signs grid when API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 503 })));
    renderWithProviders(<SignsPage />);
    expect(screen.getByRole('heading', { name: /Signes supportes/i })).toBeInTheDocument();
    expect(await screen.findByText(/API indisponible/i)).toBeInTheDocument();
    expect(screen.getByText(/عاونّي/i)).toBeInTheDocument();
  });
});
