import type { ContributionSign, ContributionSignKey } from '../types';

export const CONTRIBUTION_SIGN_KEYS: readonly ContributionSignKey[] = [
  'salam',
  'chokran',
  'tabib',
  'mosaada',
  'maa',
] as const;

export function isContributionSignKey(value: string): value is ContributionSignKey {
  return CONTRIBUTION_SIGN_KEYS.includes(value as ContributionSignKey);
}

export const DISABLED_PREVIEW_SIGNS: ContributionSign[] = [
  ['salam', 'سلام', 'salam'],
  ['chokran', 'شكرا', 'chokran'],
  ['tabib', 'طبيب', 'tabib'],
  ['mosaada', 'مساعدة', 'mosaada'],
  ['maa', 'ماء', 'maa'],
].map(([key, label_ar, transliteration]) => ({
  key: key as ContributionSignKey,
  label_ar,
  darija_transliteration: transliteration,
  reference_video_identifier: `opensigne-reference-${key}-v1`,
  reference_video_url: null,
  poster_url: `/reference-signs/posters/${key}.svg`,
  reference_video_approved: false,
  recording_instructions: `Reproduisez une seule fois le signe « ${label_ar} », puis revenez au repos.`,
  active: true,
  expected_min_duration_seconds: 2,
  expected_max_duration_seconds: 10,
}));

export function validateServerCatalog(signs: ContributionSign[]): ContributionSign[] {
  if (
    signs.length !== CONTRIBUTION_SIGN_KEYS.length ||
    signs.some((sign, index) => sign.key !== CONTRIBUTION_SIGN_KEYS[index])
  ) {
    throw new Error('Le catalogue de contribution reçu est invalide.');
  }
  return signs;
}
