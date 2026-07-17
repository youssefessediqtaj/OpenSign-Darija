import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { renderWithProviders } from '../../../test/render';
import { FingerspellingPanel } from '../components/FingerspellingPanel';

describe('FingerspellingPanel', () => {
  it('requires explicit confirmation before appending a predicted letter', () => {
    renderWithProviders(
      <FingerspellingPanel
        isModelAvailable
        isPending={false}
        onRecognize={() => undefined}
        result={{
          request_id: 'req-1',
          status: 'completed',
          model_name: 'opensign-mosl-alphabet-mock',
          model_version: '0.1.0',
          feature_schema_version: '1.0.0',
          predictions: [{ label: 'ARABIC_LETTER_ALEF', confidence: 0.72, rank: 1 }],
          unknown_probability: 0.1,
          processing_time_ms: 1,
        }}
      />,
    );
    expect(screen.getByText('ا')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Confirmer'));
    expect(screen.getAllByText('ا').length).toBeGreaterThan(1);
  });
});
