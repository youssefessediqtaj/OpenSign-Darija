import type { Message } from '../../../types/api';

export function MessageLanguageTabs({ message }: { message: Message }) {
  return (
    <dl className="grid gap-2 text-sm sm:grid-cols-2">
      <dt>Arabe</dt><dd dir="rtl" lang="ar">{message.final_darija_arabic || '—'}</dd>
      <dt>Latin</dt><dd>{message.final_darija_latin || '—'}</dd>
      <dt>Français</dt><dd>{message.final_french || '—'}</dd>
      <dt>Anglais</dt><dd>{message.final_english || '—'}</dd>
    </dl>
  );
}
