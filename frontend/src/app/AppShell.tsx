import { lazy, Suspense } from 'react';
import { useLocation } from 'react-router-dom';
import { AppLayout } from '../layouts/AppLayout';
import { AppRoutes } from '../routes';

const LandingPage = lazy(() =>
  import('../pages/LandingPage').then((module) => ({ default: module.LandingPage })),
);

/**
 * /welcome is the only route that bypasses the authenticated app shell
 * (Sidebar/Header/CommandPalette/Copilot) — it's a standalone marketing
 * entry surface. Every other path, including "/", is untouched: it still
 * renders exactly as before, inside AppLayout, through the existing
 * AppRoutes tree.
 */
export function AppShell() {
  const location = useLocation();

  if (location.pathname === '/welcome') {
    return (
      <Suspense fallback={null}>
        <LandingPage />
      </Suspense>
    );
  }

  return (
    <AppLayout>
      <AppRoutes />
    </AppLayout>
  );
}

