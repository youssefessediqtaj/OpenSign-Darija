import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Message } from '../../../types/api';
import { SpeechButton } from '../components/SpeechButton';

const message: Message = {
  id: 'message-1',
  status: 'COMPLETED',
  title: 'Test',
  raw_semantic_sequence: [],
  generated_darija_arabic: 'بغيت الما',
  generated_darija_latin: 'bghit lma',
  generated_french: null,
  generated_english: null,
  final_darija_arabic: 'بغيت الما',
  final_darija_latin: 'bghit lma',
  final_french: null,
  final_english: null,
  generation_strategy: 'template_rules',
  generation_version: '1.0.0',
  generation_metadata: {},
  is_favorite: false,
  item_count: 0,
  risk_level: 'NORMAL',
  items: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
};

beforeEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
  Object.defineProperty(window, 'speechSynthesis', {
    configurable: true,
    value: {
      getVoices: () => [{ name: 'Arabic', lang: 'ar-MA' }],
      speak: vi.fn(),
      cancel: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    },
  });
  Object.defineProperty(window, 'SpeechSynthesisUtterance', {
    configurable: true,
    value: vi.fn(function MockUtterance(this: SpeechSynthesisUtterance, text: string) {
      this.text = text;
    }),
  });
  HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  HTMLMediaElement.prototype.pause = vi.fn();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/api/v1/speech/voices')) {
      return Response.json({
        voices: [
          {
            id: 'darija-default',
            provider: 'local-darija',
            display_name: 'Voix synthétique expérimentale en Darija',
            language: 'ary-MA',
            locale: 'ary-MA',
            model_version: 'opensign-tone-v1',
            license_info: {},
            is_default: true,
            is_active: true,
            is_experimental: true,
          },
        ],
      });
    }
    if (url.endsWith('/api/v1/speech/status')) {
      return Response.json({
        mode: 'local',
        service_available: true,
        browser_fallback_enabled: true,
        voices_available: 1,
      });
    }
    return Response.json({
      generation_id: 'generation-1',
      status: 'completed',
      cache_hit: false,
      estimated_mode: 'synchronous',
      audio: {
        url: 'http://localhost:9000/opensign-speech-audio/speech/2026/07/generation-1/audio.wav',
        mime_type: 'audio/wav',
        duration_ms: 1000,
        file_size_bytes: 1200,
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      },
      voice: null,
      provider: { name: 'local-darija', model_version: 'opensign-tone-v1' },
      fallback_used: false,
      requested_language: 'ary-MA',
      synthesis_language: 'ary-MA',
    });
  }));
});

describe('SpeechButton', () => {
  it('generates audio and exposes playback controls', async () => {
    render(<SpeechButton message={message} />);
    await waitFor(() => expect(screen.getByRole('button', { name: /parler/i })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: /parler/i }));
    expect(await screen.findByLabelText('Lire')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Lire'));
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
    fireEvent.click(screen.getByLabelText('Pause'));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
  });

  it('requires confirmation for sensitive messages', async () => {
    render(<SpeechButton message={{ ...message, risk_level: 'EMERGENCY' }} />);
    await waitFor(() => expect(screen.getByRole('button', { name: /parler/i })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: /parler/i }));
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });
});
