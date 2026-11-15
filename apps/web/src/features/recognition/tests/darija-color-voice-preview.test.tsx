import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DarijaColorVoicePreview } from '../components/DarijaColorVoicePreview';

describe('DarijaColorVoicePreview', () => {
  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it('does not speak an unvalidated candidate until a user clicks', async () => {
    const play = vi.mocked(HTMLMediaElement.prototype.play);
    const view = render(<DarijaColorVoicePreview color="red" />);
    expect(screen.getByText('حمر')).toHaveAttribute('lang', 'ary');
    expect(play).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Écouter en darija' }));
    await waitFor(() => expect(play).toHaveBeenCalledOnce());
    expect(screen.getByRole('button', { name: 'Réécouter en darija' })).toBeInTheDocument();
    view.unmount();
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
  });

  it('never invokes Arabic/browser speech when a WAV cannot play', async () => {
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockRejectedValueOnce(new Error('Missing clip'));
    render(<DarijaColorVoicePreview color="orange" />);
    fireEvent.click(screen.getByRole('button', { name: 'Écouter en darija' }));
    await waitFor(() => expect(screen.getByText(/Aucun enregistrement darija approuvé/)).toBeInTheDocument());
  });
});
