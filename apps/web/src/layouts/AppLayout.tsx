import { Link, NavLink, Outlet } from 'react-router-dom';

import { useAuthStore } from '../stores/authStore';

const appItems = [
  ['/app/recognition', 'Reconnaissance'],
  ['/app/contribute', 'Contribuer'],
  ['/app/messages', 'Messages'],
  ['/app/settings', 'Parametres'],
  ['/admin/reviews/linguistic', 'Review'],
  ['/admin/datasets/external', 'Datasets publics'],
  ['/admin/models', 'Modeles'],
  ['/admin/linguistics', 'Linguistique'],
  ['/admin/speech', 'Speech'],
];

export function AppLayout() {
  const { user, logout } = useAuthStore();
  return (
    <div className="min-h-screen bg-slate-50 text-ink dark:bg-slate-950 dark:text-slate-50">
      <header className="border-b bg-white dark:border-slate-800 dark:bg-slate-900">
        <nav className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4" aria-label="Navigation application">
          <Link to="/app" className="font-bold">
            OpenSign Darija
          </Link>
          <div className="flex flex-wrap gap-2">
            {appItems.map(([to, label]) => (
              <NavLink key={to} to={to} className={({ isActive }) => `rounded-md px-3 py-2 text-sm ${isActive ? 'bg-teal-100 text-teal-900 dark:bg-teal-900 dark:text-white' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                {label}
              </NavLink>
            ))}
            <button className="rounded-md px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800" onClick={logout}>
              {user ? 'Deconnexion' : 'Session demo'}
            </button>
          </div>
        </nav>
      </header>
      <main id="main" className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
