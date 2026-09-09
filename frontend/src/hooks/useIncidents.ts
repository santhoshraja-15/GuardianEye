import { useQuery } from '@tanstack/react-query';
import { getIncidents } from '../api/incidents';

export function useIncidents() {
  return useQuery({
    queryKey: ['incidents'],
    queryFn: getIncidents,
  });
}

