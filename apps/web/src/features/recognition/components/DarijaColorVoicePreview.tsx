import { Button } from '../../../shared/ui/Button';
import { DARIJA_COLOR_WORDS, type DarijaColor } from '../domain/darija-colors';
import { speechProviderRegistry } from '../domain/darija-voice-provider';
import { useDarijaColorAudio } from '../hooks/useDarijaColorAudio';

export function DarijaColorVoicePreview({ color }: { color: DarijaColor }) {
  const { status, play, stop } = useDarijaColorAudio(color);
  const asset = speechProviderRegistry.local.resolve(color);
  const message = {
    stopped: 'Lecture arrêtée.',
    loading: 'Chargement vocal…',
    playing: 'Lecture en cours.',
    unavailable: 'Enregistrement indisponible ou illisible. Aucun repli en arabe standard.',
  }[status];
  return (
    <section aria-label="Aperçu vocal Darija" className="mt-4 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
      <p className="text-sm font-semibold">Parole en darija marocaine — aperçu manuel</p>
      <p className="mt-2 text-2xl font-bold" lang="ary" dir="rtl">{DARIJA_COLOR_WORDS[color]}</p>
      <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">
        Texte provisoire à vérifier. Le candidat est expérimental : la voix ne valide pas la reconnaissance.
      </p>
      <p className="mt-2 text-xs">{asset ? `Audio approuvé · version ${asset.version}` : "Audio non approuvé ou absent · version indisponible"}</p>
      <Button variant="secondary" type="button" className="mt-3" onClick={play}>
        {status === 'playing' ? 'Réécouter en darija' : 'Écouter en darija'}
      </Button>
      {(status === 'playing' || status === 'loading') && (
        <Button variant="ghost" type="button" className="mt-3" onClick={stop}>Arrêter la lecture</Button>
      )}
      <p className="mt-2 text-sm" role="status" aria-live="polite">{message}</p>
    </section>
  );
}
