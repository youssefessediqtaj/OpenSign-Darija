import { useState } from 'react';

import { Button } from '../../../components/Button';
import type { Message } from '../../../types/api';
import { copyText, shareText } from '../services/message-share.service';

export function ShareMessageButton({ message }: { message: Message }) {
  const [status, setStatus] = useState('');
  const text = message.final_darija_arabic || message.generated_darija_arabic || '';
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="secondary" onClick={async () => { await copyText(text); setStatus('Copie effectuee.'); }}>Copier</Button>
      <Button variant="secondary" onClick={async () => { await shareText(text); setStatus('Partage prepare.'); }}>Partager</Button>
      {status && <span className="text-sm text-slate-600 dark:text-slate-300">{status}</span>}
    </div>
  );
}
