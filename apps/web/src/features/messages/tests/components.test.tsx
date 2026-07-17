import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../../test/render';
import type { GenerationResponse, Message } from '../../../types/api';
import { GeneratedMessagePanel } from '../components/GeneratedMessagePanel';
import { ManualTextEditor } from '../components/ManualTextEditor';
import { MessageTimeline } from '../components/MessageTimeline';

const message: Message = {
  id: 'msg-1',
  status: 'READY',
  title: 'Test',
  raw_semantic_sequence: ['ACTION_WANT', 'OBJECT_WATER'],
  generated_darija_arabic: 'بغيت الما',
  generated_darija_latin: 'bghit lma',
  generated_french: "Je veux de l'eau.",
  generated_english: 'I want water.',
  final_darija_arabic: 'بغيت الما',
  final_darija_latin: 'bghit lma',
  final_french: "Je veux de l'eau.",
  final_english: 'I want water.',
  generation_strategy: 'template_rules',
  generation_version: '1.0.0',
  generation_metadata: {},
  is_favorite: false,
  item_count: 2,
  risk_level: 'NORMAL',
  items: [
    {
      id: 'item-1',
      position: 1,
      item_type: 'CONFIRMED_SIGN',
      sign_id: 'want',
      semantic_concept_id: 'concept-want',
      semantic_concept_code: 'ACTION_WANT',
      recognition_session_id: 'rec-1',
      source: 'USER_CORRECTION',
      display_label: 'vouloir',
      metadata: {},
      created_at: '2026-07-17T00:00:00Z',
    },
    {
      id: 'item-2',
      position: 2,
      item_type: 'CONFIRMED_SIGN',
      sign_id: 'water',
      semantic_concept_id: 'concept-water',
      semantic_concept_code: 'OBJECT_WATER',
      recognition_session_id: 'rec-2',
      source: 'USER_CORRECTION',
      display_label: 'eau',
      metadata: {},
      created_at: '2026-07-17T00:00:00Z',
    },
  ],
  created_at: '2026-07-17T00:00:00Z',
  updated_at: '2026-07-17T00:00:00Z',
};

describe('message components', () => {
  it('renders semantic items with keyboard move controls', () => {
    const onMove = vi.fn();
    renderWithProviders(<MessageTimeline message={message} onMove={onMove} onRemove={vi.fn()} />);
    fireEvent.click(screen.getAllByLabelText(/Descendre/i)[0]);
    expect(onMove).toHaveBeenCalledWith('item-1', 1);
    expect(screen.getByText('ACTION_WANT · USER_CORRECTION')).toBeInTheDocument();
  });

  it('shows generated Darija and incomplete warnings', () => {
    const generation: GenerationResponse = {
      message_id: 'msg-1',
      generation_version: '1.0.0',
      strategy: 'template_rules',
      semantic_sequence: ['ACTION_WANT'],
      result: { darija_arabic: 'بغيت', darija_latin: 'bghit', french: '', english: '' },
      template: null,
      linguistic_status: 'INCOMPLETE',
      system_insertions: [],
      warnings: ['Phrase incomplete: ajoutez OBJECT.'],
      alternatives: [],
    };
    renderWithProviders(<GeneratedMessagePanel message={{ ...message, generated_darija_arabic: 'بغيت' }} generation={generation} />);
    expect(screen.getByText('Phrase incomplete')).toBeInTheDocument();
    expect(screen.getByText('بغيت')).toHaveAttribute('dir', 'rtl');
  });

  it('keeps manual Arabic and Latin edits independent', () => {
    const onChange = vi.fn();
    renderWithProviders(<ManualTextEditor message={message} onChange={onChange} saveState="SAVED" />);
    fireEvent.change(screen.getByLabelText(/Darija arabe/i), { target: { value: 'عاونوني دابا' } });
    expect(onChange).toHaveBeenCalledWith({ final_darija_arabic: 'عاونوني دابا' });
    expect(onChange).not.toHaveBeenCalledWith({ final_darija_latin: expect.any(String) });
  });
});
