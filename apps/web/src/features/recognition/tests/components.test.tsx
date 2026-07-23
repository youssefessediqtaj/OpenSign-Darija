import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { CameraPermissionPanel } from '../components/CameraPermissionPanel';
import { CameraPreview } from '../components/CameraPreview';
import { RecognitionWorkspace } from '../components/RecognitionWorkspace';

describe('minimal recognition interface', () => {
  it('offers camera activation as the only initial action', () => {
    render(<RecognitionWorkspace />);
    expect(screen.getByText('OpenSigne Darija')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Reconnaissance de signes' })).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Activer la caméra' })).toBeInTheDocument();
    expect(screen.queryByText(/connexion|mode|alphabet|capture manuelle/i)).not.toBeInTheDocument();
  });

  it('activates the permission callback', async () => {
    const onEnable = vi.fn();
    render(<CameraPermissionPanel onEnable={onEnable} errorMessage={null} isRequesting={false} />);
    await userEvent.click(screen.getByRole('button', { name: 'Activer la caméra' }));
    expect(onEnable).toHaveBeenCalledOnce();
  });

  it('renders an accessible inactive preview', () => {
    render(
      <CameraPreview stream={null} videoRef={{ current: null }} isMirrored={false}>
        {null}
      </CameraPreview>,
    );
    expect(screen.getByText('La caméra n’est pas active.')).toBeInTheDocument();
  });
});
