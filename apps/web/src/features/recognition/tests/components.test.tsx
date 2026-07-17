import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../../test/render';
import { CameraPermissionPanel } from '../components/CameraPermissionPanel';
import { CameraPreview } from '../components/CameraPreview';
import { FramingGuide } from '../components/FramingGuide';
import { PredictionPanel } from '../components/PredictionPanel';
import { evaluateFraming } from '../utils/framing-evaluator';
import { createSyntheticFrame } from '../services/holistic.service';

describe('recognition components', () => {
  it('renders the permission panel', () => {
    renderWithProviders(
      <CameraPermissionPanel onEnable={vi.fn()} errorMessage={null} isRequesting={false} />,
    );
    expect(screen.getByRole('button', { name: /Activer la camera/i })).toBeInTheDocument();
  });

  it('renders preview placeholder', () => {
    renderWithProviders(
      <CameraPreview stream={null} videoRef={{ current: null }} isMirrored={false}>
        <span />
      </CameraPreview>,
    );
    expect(screen.getByText(/camera n’est pas active/i)).toBeInTheDocument();
  });

  it('renders framing guide', () => {
    renderWithProviders(<FramingGuide evaluation={evaluateFraming(createSyntheticFrame(1, 100))} />);
    expect(screen.getByText(/correctement positionne/i)).toBeInTheDocument();
  });

  it('renders prediction panel result', () => {
    renderWithProviders(
      <PredictionPanel
        result={{
          recognition_id: 'rec',
          request_id: 'req',
          status: 'completed',
          model_name: 'mock',
          model_version: '0.2.0',
          inference_mode: 'mock',
          decision: 'known',
          confidence_level: 'high',
          predictions: [{ prediction_id: 'pred', label: 'aide', confidence: 0.79, rank: 1 }],
          unknown_probability: 0.03,
          processing_time_ms: 10,
        }}
      />,
    );
    expect(screen.getByText(/Reconnaissance expérimentale/i)).toBeInTheDocument();
    expect(screen.getByText(/Mode developpement/i)).toBeInTheDocument();
    expect(screen.getByText('0.2.0')).toBeInTheDocument();
  });
});
