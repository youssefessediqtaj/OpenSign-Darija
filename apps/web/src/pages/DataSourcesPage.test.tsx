import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { renderWithProviders } from '../test/render';
import { DataSourcesPage } from './DataSourcesPage';

describe('DataSourcesPage', () => {
  it('shows Mendeley as data source and ScienceDirect as reference', () => {
    renderWithProviders(<DataSourcesPage />);
    expect(screen.getByText(/Mendeley Data/i)).toBeInTheDocument();
    expect(screen.getByText(/10.17632\/23phgyt3mt.1/i)).toBeInTheDocument();
    expect(screen.getByText(/pas comme source de données distincte/i)).toBeInTheDocument();
    expect(screen.getByText(/À vérifier/i)).toBeInTheDocument();
  });
});
