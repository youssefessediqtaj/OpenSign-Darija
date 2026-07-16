import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { HomePage } from './HomePage';
import { renderWithProviders } from '../test/render';

describe('HomePage', () => {
  it('renders the project introduction', () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByRole('heading', { name: /OpenSign Darija/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Essayer la demonstration/i })).toBeInTheDocument();
    expect(screen.getByText(/ne remplace pas un interprete professionnel/i)).toBeInTheDocument();
  });
});
