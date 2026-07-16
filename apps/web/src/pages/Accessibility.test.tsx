import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PublicLayout } from '../layouts/PublicLayout';
import { renderWithProviders } from '../test/render';

describe('accessibility basics', () => {
  it('renders a skip link and labelled navigation', () => {
    renderWithProviders(<PublicLayout />);
    expect(screen.getByRole('link', { name: /Aller au contenu principal/i })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /Navigation principale/i })).toBeInTheDocument();
  });
});
