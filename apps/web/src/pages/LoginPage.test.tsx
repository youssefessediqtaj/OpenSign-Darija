import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { LoginPage } from './LoginPage';
import { renderWithProviders } from '../test/render';

describe('LoginPage', () => {
  it('validates required login fields', async () => {
    renderWithProviders(<LoginPage />);
    await userEvent.click(screen.getByRole('button', { name: /se connecter/i }));
    expect(await screen.findByText(/Adresse e-mail invalide/i)).toBeInTheDocument();
    expect(screen.getByText(/Mot de passe requis/i)).toBeInTheDocument();
  });
});
