import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuthStore } from '../stores/authStore';

export function ProtectedRoute() {
  const location = useLocation();
  const tokens = useAuthStore((state) => state.tokens);
  if (location.pathname === '/app/recognition') {
    return <Outlet />;
  }
  if (!tokens) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
