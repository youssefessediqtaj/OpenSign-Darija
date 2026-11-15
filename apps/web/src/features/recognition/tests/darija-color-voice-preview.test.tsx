import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../domain/darija-voice-provider', () => ({
  speechProviderRegistry: { local: { resolve: (color: string) => ({ url: `/audio/darija/colors/${color}.wav`, version: 'fixture', format: 'audio/wav', sha256: 'a'.repeat(64) }) } },
}));

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
    await waitFor(() => expect(screen.getByText(/Enregistrement indisponible ou illisible/)).toBeInTheDocument());
  });
  it('stops old audio on color change and ignores delayed play completion', async () => {
    let resolvePlay: (() => void) | undefined;
    vi.mocked(HTMLMediaElement.prototype.play).mockImplementationOnce(() => new Promise<void>((resolve) => { resolvePlay = resolve; }));
    const view = render(<DarijaColorVoicePreview color="red" />);
    fireEvent.click(screen.getByRole('button', { name: 'Écouter en darija' }));
    expect(screen.getByRole('status')).toHaveTextContent('Chargement');
    view.rerender(<DarijaColorVoicePreview color="blue" />);
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
    await act(async () => resolvePlay?.());
    expect(screen.getByRole('status')).toHaveTextContent('arrêtée');
  });

  it('cancels on stop and releases each replaced player', async () => {
    const view = render(<DarijaColorVoicePreview color="red" />);
    fireEvent.click(screen.getByRole('button', { name: 'Écouter en darija' }));
    fireEvent.click(screen.getByRole('button', { name: 'Écouter en darija' }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Lecture en cours'));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Arrêter la lecture' }));
    expect(screen.getByRole('status')).toHaveTextContent('arrêtée');
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledTimes(2);
    view.unmount();
  });

});
