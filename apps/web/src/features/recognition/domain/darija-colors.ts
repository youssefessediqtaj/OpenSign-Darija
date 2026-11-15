/** Explicit, provisional Moroccan Darija vocabulary for nine COLORS_V1 semantic classes. 
 * Written forms and recorded pronunciations require review by native Darija speakers.
 * This map is not evidence that a sign is linguistically correct.
 */
export const DARIJA_COLOR_WORDS = {
  black: 'كحل',
  blue: 'زرق',
  brown: 'قهوي',
  green: 'خضر',
  orange: 'ليموني',
  pink: 'وردي',
  red: 'حمر',
  white: 'بيض',
  yellow: 'صفر',
} as const;

export type DarijaColor = keyof typeof DARIJA_COLOR_WORDS;

export function isDarijaColor(value: string): value is DarijaColor {
  return Object.prototype.hasOwnProperty.call(DARIJA_COLOR_WORDS, value);
}

export function darijaColorAudioUrl(color: DarijaColor, baseUrl = import.meta.env.BASE_URL): string {
  const base = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  return `${base}audio/darija/colors/${color}.wav`;
}
