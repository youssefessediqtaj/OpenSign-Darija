import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { systemApi } from '../services/systemApi';
import { useAuthStore } from '../stores/authStore';

export function AppDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const version = useQuery({ queryKey: ['api-version'], queryFn: systemApi.version, retry: false });
  const tiles = [
    ['/app/recognition', 'Reconnaissance', 'Tester le flux de prediction simule.'],
    ['/app/messages', 'Messages', 'Preparer les phrases Darija confirmees.'],
    ['/app/settings', 'Parametres', 'Gerer les preferences d’accessibilite.'],
  ];
  return (
    <section>
      <h1 className="text-3xl font-bold">Tableau de bord</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">Etat de connexion: {user ? user.email : 'session locale de demonstration'}</p>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {tiles.map(([to, title, description]) => (
          <Link key={to} to={to} className="rounded-md border border-slate-200 bg-white p-5 hover:border-cedar dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-xl font-semibold">{title}</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{description}</p>
          </Link>
        ))}
      </div>
      <dl className="mt-8 grid gap-4 md:grid-cols-2">
        <div className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <dt className="font-semibold">Version backend</dt>
          <dd>{version.data?.version ?? 'indisponible'}</dd>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <dt className="font-semibold">Version inference</dt>
          <dd>0.1.0 mock</dd>
        </div>
      </dl>
    </section>
  );
}
