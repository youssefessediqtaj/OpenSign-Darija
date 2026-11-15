import { useEffect, useRef, useState } from 'react';

import { DARIJA_COLOR_WORDS, isDarijaColor, type DarijaColor } from '../domain/darija-colors';

/** Local files stay in this browser tab and are never sent to recognition or speech APIs. */
export function PrivateVoicePackPreview() {
  const [files, setFiles] = useState<Partial<Record<DarijaColor, File>>>({});
  const [selected, setSelected] = useState<DarijaColor>('black');
  const [message, setMessage] = useState('Sélectionnez les neuf fichiers WAV privés.');
  const [url, setUrl] = useState<string | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const selectedFile = files[selected];

  useEffect(() => {
    if (!selectedFile) { setUrl(null); return; }
    const next = URL.createObjectURL(selectedFile);
    setUrl(next);
    return () => { URL.revokeObjectURL(next); };
  }, [selectedFile]);

  useEffect(() => {
    const player = audio.current;
    return () => { player?.pause(); };
  }, [url]);

  function loadFiles(list: FileList | null) {
    audio.current?.pause();
    const next: Partial<Record<DarijaColor, File>> = {};
    const input = Array.from(list ?? []);
    for (const file of input) {
      const match = /^([a-z]+)\.wav$/.exec(file.name);
      const label = match?.[1] ?? '';
      if (!isDarijaColor(label) || next[label]) {
        setFiles({}); setMessage('Fichiers invalides ou doublons : sélectionnez les neuf WAV nommés par couleur.'); return;
      }
      next[label] = file;
    }
    if (input.length !== 9 || Object.keys(next).length !== 9) {
      setFiles({}); setMessage('Neuf couleurs distinctes sont requises.'); return;
    }
    setFiles(next);
    setMessage('Aperçu privé uniquement : prononciation, qualité et diffusion non approuvées.');
  }

  return (
    <section aria-label="Aperçu privé des enregistrements" className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
      <h3 className="font-semibold">Aperçu privé des enregistrements</h3>
      <p className="mt-1 text-sm">Sélectionnez les neuf WAV sur cet appareil. Ils restent dans cet onglet et ne sont pas publiés.</p>
      <label className="mt-2 block text-sm" htmlFor="private-voice-files">Fichiers WAV privés</label>
      <input id="private-voice-files" type="file" accept=".wav,audio/wav" multiple onChange={(event) => loadFiles(event.target.files)} />
      <p role="status" className="mt-2 text-sm">{message}</p>
      {selectedFile && <>
        <label className="mt-3 block text-sm" htmlFor="private-voice-color">Couleur à écouter</label>
        <select id="private-voice-color" className="text-slate-900" value={selected} onChange={(event) => {
          if (isDarijaColor(event.target.value)) { audio.current?.pause(); setSelected(event.target.value); }
        }}>
          {Object.entries(DARIJA_COLOR_WORDS).map(([color, word]) => <option key={color} value={color}>{color} — {word}</option>)}
        </select>
        <p lang="ary" dir="rtl" className="mt-2 text-lg">{DARIJA_COLOR_WORDS[selected]}</p>
        {url && <audio key={url} ref={audio} controls preload="none" src={url} aria-label={`Enregistrement privé ${selected}`} className="mt-2 max-w-full" />}
      </>}
    </section>
  );
}
