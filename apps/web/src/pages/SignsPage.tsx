import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { useState } from 'react';

import { signsApi } from '../services/signsApi';

const fallbackSigns = [
  { slug: 'oui', canonical_meaning: 'oui', darija_arabic: 'إيه', darija_latin: 'iyeh', category: { slug: 'questions', name_fr: 'Questions' }, status: 'ACTIVE' },
  { slug: 'aide', canonical_meaning: 'aide', darija_arabic: 'عاونّي', darija_latin: 'aweni', category: { slug: 'besoins-essentiels', name_fr: 'Besoins essentiels' }, status: 'ACTIVE' },
  { slug: 'medecin', canonical_meaning: 'medecin', darija_arabic: 'طبيب', darija_latin: 'tbib', category: { slug: 'sante', name_fr: 'Sante' }, status: 'EXPERIMENTAL' },
];

export function SignsPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const signsQuery = useQuery({ queryKey: ['signs', search, category], queryFn: () => signsApi.list(search, category), retry: false });
  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: signsApi.categories, retry: false });
  const signs = signsQuery.data?.items ?? fallbackSigns;

  return (
    <section className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold">Signes supportes</h1>
      <div className="mt-6 grid gap-3 md:grid-cols-[1fr_240px]">
        <label className="relative">
          <span className="sr-only">Recherche</span>
          <Search className="absolute left-3 top-3 h-5 w-5 text-slate-500" aria-hidden="true" />
          <input className="min-h-11 w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 dark:border-slate-700 dark:bg-slate-900" placeholder="Rechercher un signe" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label>
          <span className="sr-only">Categorie</span>
          <select className="min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 dark:border-slate-700 dark:bg-slate-900" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Toutes les categories</option>
            {(categoriesQuery.data ?? []).map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.name_fr}
              </option>
            ))}
          </select>
        </label>
      </div>
      {signsQuery.isError && <p className="mt-4 text-sm text-coral">API indisponible: affichage de donnees simulees.</p>}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {signs.map((sign) => (
          <article key={sign.slug} className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-xl font-semibold">{sign.canonical_meaning}</h2>
              <span className="rounded-md bg-teal-100 px-2 py-1 text-xs font-semibold text-teal-900 dark:bg-teal-900 dark:text-teal-50">{sign.status}</span>
            </div>
            <p className="mt-4 text-2xl" lang="ar" dir="rtl">{sign.darija_arabic}</p>
            <p className="mt-1 text-slate-700 dark:text-slate-300">{sign.darija_latin}</p>
            <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">{sign.category.name_fr}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
