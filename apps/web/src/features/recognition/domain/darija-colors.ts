/** The user confirmed the written forms for this prototype; audio and sign mapping remain unreviewed. */
export const DARIJA_COLOR_WORDS = {
  black: 'كحل', blue: 'زرق', brown: 'قهوي', green: 'خضر', orange: 'ليموني',
  pink: 'وردي', red: 'حمر', white: 'بيض', yellow: 'صفر',
} as const;

export type DarijaColor = keyof typeof DARIJA_COLOR_WORDS;
export type VocabularyEntry = {
  id: DarijaColor;
  expression: string;
  regionalAlternatives: readonly string[];
  pronunciationNotes: string;
  reviewStatus: 'pending' | 'approved' | 'rejected';
  reviewerReference: string | null;
  audioReference: string;
  audioApprovalStatus: 'pending' | 'approved' | 'rejected';
  version: string;
};

export const DARIJA_VOCABULARY = Object.fromEntries(
  Object.entries(DARIJA_COLOR_WORDS).map(([id, expression]) => [id, {
    id, expression, regionalAlternatives: [],
    pronunciationNotes: id === 'orange' ? 'Meaning and adjective versus color name need review.' : 'Pronunciation and standalone usage require review.',
    reviewStatus: 'approved', reviewerReference: 'prototype-speaker-confirmation', audioReference: `${id}.wav`,
    audioApprovalStatus: 'pending', version: '1',
  }]),
) as unknown as Record<DarijaColor, VocabularyEntry>;

export function isDarijaColor(value: string): value is DarijaColor {
  return Object.prototype.hasOwnProperty.call(DARIJA_COLOR_WORDS, value);
}
