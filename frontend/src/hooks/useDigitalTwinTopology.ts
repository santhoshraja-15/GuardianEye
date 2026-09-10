import { useQuery } from '@tanstack/react-query';
import { getDigitalTwinTopology } from '../api/digital-twin';

// Query key must match the ['digital-twin'] prefix realtime.ts
// invalidates on SPATIAL_EVENT_CREATED so a new zone-transition/
// proximity event actually refreshes this page instead of only
// invalidating a cache nothing reads from.
export function useDigitalTwinTopology() {
  return useQuery({
    queryKey: ['digital-twin', 'topology'],
    queryFn: getDigitalTwinTopology,
    retry: false,
  });
}
