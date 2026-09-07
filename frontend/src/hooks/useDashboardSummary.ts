import { useQuery } from '@tanstack/react-query';
import { getDashboardSummary } from '../api/analytics';
import { useSessionStore } from '../stores/session-store';

export function useDashboardSummary() {
  // Guard against firing on public/unauthenticated routes — see useAlerts()
  // for why an authenticated-only query must not run before login.
  const isAuthenticated = useSessionStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
    enabled: isAuthenticated,
  });
}
