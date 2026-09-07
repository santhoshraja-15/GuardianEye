import { useQuery } from '@tanstack/react-query';
import { getAlerts } from '../api/alerts';
import { useSessionStore } from '../stores/session-store';

export function useAlerts() {
  // AppLayout (which reads this for the alert badge) also renders on public
  // routes like /login, before any session exists — fetching there would
  // hit a real 401 and, via the API client's no-refresh-token path, hard-
  // redirect back to /login, reloading the page and refiring this query
  // forever. Only fetch once actually authenticated.
  const isAuthenticated = useSessionStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: ['alerts'],
    queryFn: getAlerts,
    enabled: isAuthenticated,
  });
}
