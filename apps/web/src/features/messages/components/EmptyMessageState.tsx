import { Button } from '../../../components/Button';

export function EmptyMessageState({ onCreate }: { onCreate: () => void }) {
  return (
    <section className="rounded-md border border-dashed border-slate-300 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-xl font-semibold">Aucun message ouvert</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        Creez un brouillon pour combiner des signes confirmes, generer une phrase Darija, puis garder le controle du texte final.
      </p>
      <Button className="mt-4" onClick={onCreate}>Créer un nouveau message</Button>
    </section>
  );
}
