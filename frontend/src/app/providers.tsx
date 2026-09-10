import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useEffect, useState } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { getDigitalTwinTopology } from '../api/digital-twin';
import { RealtimeSocketManager } from '../services/realtime';
import { useAppStore } from '../stores/app-store';
import { useSessionStore } from '../stores/session-store';

interface AppProvidersProps {
  children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  }));

  const [manager] = useState(
    () => new RealtimeSocketManager(
      queryClient,
      () => useSessionStore.getState().accessToken,
      // The realtime join key must be the real warehouse UUID, not the
      // sidebar's display label (selectedWarehouseId, historically the
      // literal string "Warehouse 01") — the backend broadcasts to the
      // resolved warehouse UUID (ai/pipeline_runner.py), so connecting
      // with anything else joined a room nothing was ever sent to.
      () => useAppStore.getState().resolvedWarehouseId,
      (state) => useAppStore.getState().setConnectionState(state),
    ),
  );

  const accessToken = useSessionStore((state) => state.accessToken);
  const resolvedWarehouseId = useAppStore((state) => state.resolvedWarehouseId);
  const setResolvedWarehouseId = useAppStore((state) => state.setResolvedWarehouseId);

  // Resolve the real warehouse UUID once at startup — any endpoint that
  // returns it works; the digital-twin topology endpoint already needs
  // to exist and already resolves "the" warehouse when no ID is given.
  useEffect(() => {
    if (resolvedWarehouseId) return;
    let cancelled = false;
    getDigitalTwinTopology()
      .then((topology) => {
        if (!cancelled) setResolvedWarehouseId(topology.warehouse_id);
      })
      .catch(() => {
        // No warehouse configured yet — realtime simply stays
        // disconnected (RealtimeSocketManager already handles a null
        // warehouse id as OFFLINE) rather than guessing an id.
      });
    return () => {
      cancelled = true;
    };
  }, [resolvedWarehouseId, setResolvedWarehouseId]);

  useEffect(() => {
    manager.connect();
    return () => {
      manager.disconnect();
    };
  }, [accessToken, manager, resolvedWarehouseId]);

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
  );
}
