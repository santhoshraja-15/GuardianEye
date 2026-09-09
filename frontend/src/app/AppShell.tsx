import { AppLayout } from '../layouts/AppLayout';
import { AppRoutes } from '../routes';

export function AppShell() {
  return (
    <AppLayout>
      <AppRoutes />
    </AppLayout>
  );
}

