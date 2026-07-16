import { Link, NavLink, Outlet } from 'react-router-dom';

import { SkipLink } from '../components/SkipLink';

const navItems = [
  ['/', 'Accueil'],
  ['/demo', 'Demo'],
  ['/signs', 'Signes'],
  ['/about', 'A propos'],
  ['/accessibility', 'Accessibilite'],
];

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-mist text-ink dark:bg-slate-950 dark:text-slate-50">
      <SkipLink />
      <header className="border-b border-slate-200 bg-white/95 dark:border-slate-800 dark:bg-slate-900">
        <nav className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4" aria-label="Navigation principale">
          <Link to="/" className="text-lg font-bold">
            OpenSign Darija
          </Link>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {navItems.map(([to, label]) => (
              <NavLink key={to} to={to} className={({ isActive }) => `rounded-md px-3 py-2 ${isActive ? 'bg-teal-100 text-teal-900 dark:bg-teal-900 dark:text-white' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                {label}
              </NavLink>
            ))}
            <NavLink to="/login" className="rounded-md border border-cedar px-3 py-2 text-cedar">
              Connexion
            </NavLink>
          </div>
        </nav>
      </header>
      <main id="main">
        <Outlet />
      </main>
    </div>
  );
}
