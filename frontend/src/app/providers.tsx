import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useEffect, useState } from 'react';
import { BrowserRouter } from 'react-router-dom';
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
      () => useAppStore.getState().selectedWarehouseId,
      (state) => useAppStore.getState().setConnectionState(state),
    ),
  );

  const accessToken = useSessionStore((state) => state.accessToken);
  const selectedWarehouseId = useAppStore((state) => state.selectedWarehouseId);

  // Sync the persisted theme to the <html data-theme="…"> attribute.
  // This runs on mount and whenever the user toggles the theme, giving
  // instant no-reload switching via the CSS [data-theme="light"] overrides.
  const theme = useAppStore((state) => state.theme);
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    manager.connect();
    return () => {
      manager.disconnect();
    };
  }, [accessToken, manager, selectedWarehouseId]);

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
  );
}
