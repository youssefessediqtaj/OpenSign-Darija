import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { RegisterPage } from './RegisterPage';
import { renderWithProviders } from '../test/render';

describe('RegisterPage', () => {
  it('validates password confirmation and terms', async () => {
    renderWithProviders(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/Nom d'affichage/i), 'Demo');
    await userEvent.type(screen.getByLabelText(/E-mail/i), 'demo@example.com');
    await userEvent.type(screen.getByLabelText(/^Mot de passe$/i), 'strongpass1');
    await userEvent.type(screen.getByLabelText(/Confirmation/i), 'different1');
    await userEvent.click(screen.getByRole('button', { name: /creer le compte/i }));
    expect(await screen.findByText(/ne correspondent pas/i)).toBeInTheDocument();
    expect(screen.getByText(/Acceptation requise/i)).toBeInTheDocument();
  });
});
