import { ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '../components/Button';

export function HomePage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-10 px-4 py-14 md:grid-cols-[1.2fr_0.8fr] md:items-center">
      <div className="space-y-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-cedar">Prototype open source en developpement</p>
        <h1 className="text-4xl font-bold leading-tight md:text-6xl">OpenSign Darija</h1>
        <p className="max-w-2xl text-lg leading-8 text-slate-700 dark:text-slate-300">
          Une base web accessible pour preparer la reconnaissance de signes de la Langue des Signes Marocaine, la construction de messages en Darija et une future lecture vocale.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link to="/demo">
            <Button>Essayer la demonstration</Button>
          </Link>
          <a href="https://github.com/" target="_blank" rel="noreferrer">
            <Button variant="secondary">
              Voir le projet open source <ExternalLink className="ml-2 inline h-4 w-4" aria-hidden="true" />
            </Button>
          </a>
        </div>
        <p className="max-w-2xl rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
          Ce prototype ne remplace pas un interprete professionnel et ne doit pas etre presente comme medicalement ou juridiquement certifie.
        </p>
      </div>
      <div className="rounded-md border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="aspect-video rounded-md bg-slate-900 p-4 text-white">
          <div className="flex h-full flex-col justify-between">
            <span className="text-sm text-teal-200">Flux camera simule</span>
            <div className="grid grid-cols-3 gap-2">
              <span className="h-16 rounded-md bg-teal-500/40" />
              <span className="h-16 rounded-md bg-white/20" />
              <span className="h-16 rounded-md bg-coral/50" />
            </div>
            <span className="text-sm">Prediction mock: medecin - 82%</span>
          </div>
        </div>
      </div>
    </section>
  );
}
