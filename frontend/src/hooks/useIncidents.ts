import { useQuery } from '@tanstack/react-query';
import { getIncidents } from '../api/incidents';
import { useSessionStore } from '../stores/session-store';

export function useIncidents() {
  // Guard against firing on public/unauthenticated routes — see useAlerts()
  // for why an authenticated-only query must not run before login.
  const isAuthenticated = useSessionStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: ['incidents'],
    queryFn: getIncidents,
    enabled: isAuthenticated,
  });
}
