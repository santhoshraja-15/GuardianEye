import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  // Human-readable label shown in the sidebar — never sent anywhere.
  selectedWarehouseId: string | null;
  // The REAL warehouse UUID, resolved once at startup from
  // GET /digital-twin/topology (see app/providers.tsx). The realtime
  // websocket join and the backend's broadcast room key must use this,
  // not selectedWarehouseId's display label — connecting with the
  // literal string "Warehouse 01" (the previous default/only value)
  // joined a room the backend never broadcasts to, silently no-oping
  // every realtime event regardless of the event-name fix.
  resolvedWarehouseId: string | null;
  // Set by DigitalTwinPage when the operator picks "view source video"
  // on a tracked entity; consumed and cleared once by LiveStreamsPage
  // on mount — a minimal, real cross-page link between the twin and
  // the video it came from (spec section 14/45) without a bigger
  // shared-selection framework.
  pendingFocusVideoId: string | null;
  sidebarCollapsed: boolean;
  connectionState: 'LIVE' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE';
  setSelectedWarehouseId: (warehouseId: string | null) => void;
  setResolvedWarehouseId: (warehouseId: string | null) => void;
  setPendingFocusVideoId: (videoId: string | null) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setConnectionState: (state: AppState['connectionState']) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedWarehouseId: 'Warehouse 01',
      resolvedWarehouseId: null,
      pendingFocusVideoId: null,
      sidebarCollapsed: false,
      connectionState: 'LIVE',
      setSelectedWarehouseId: (warehouseId) => set({ selectedWarehouseId: warehouseId }),
      setResolvedWarehouseId: (warehouseId) => set({ resolvedWarehouseId: warehouseId }),
      setPendingFocusVideoId: (videoId) => set({ pendingFocusVideoId: videoId }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setConnectionState: (state) => set({ connectionState: state }),
    }),
    {
      name: 'guardianeye-app',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        selectedWarehouseId: state.selectedWarehouseId,
      }),
    },
  ),
);
