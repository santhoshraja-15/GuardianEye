import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'dark' | 'light';

interface AppState {
  selectedWarehouseId: string | null;
  sidebarCollapsed: boolean;
  connectionState: 'LIVE' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE';
  theme: Theme;
  setSelectedWarehouseId: (warehouseId: string | null) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setConnectionState: (state: AppState['connectionState']) => void;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedWarehouseId: 'Warehouse 01',
      sidebarCollapsed: false,
      connectionState: 'LIVE',
      theme: 'dark',
      setSelectedWarehouseId: (warehouseId) => set({ selectedWarehouseId: warehouseId }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setConnectionState: (state) => set({ connectionState: state }),
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'guardianeye-app',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
        selectedWarehouseId: state.selectedWarehouseId,
      }),
    },
  ),
);
