import { ReactNode, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { CopilotChatDrawer } from '../components/copilot/CopilotChatDrawer';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { useAlerts } from '../hooks/useAlerts';
import { useAppStore } from '../stores/app-store';
import { useSessionStore } from '../stores/session-store';

interface AppLayoutProps {
  children: ReactNode;
}

const pageTitles: Record<string, string> = {
  '/': 'Overview',
  '/live': 'Live Streams',
  '/analysis': 'Video Intelligence',
  '/incidents': 'Incident Board',
  '/evidence': 'Evidence Vault',
  '/prevention': 'Prevention Studio',
  '/digital-twin': 'Digital Twin',
  '/dna': 'Behaviour DNA',
  '/analytics': 'Analytics',
  '/human-review': 'Human Review',
};

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useSessionStore();
  const { sidebarCollapsed, toggleSidebar, selectedWarehouseId, connectionState } = useAppStore();
  const { data: alerts } = useAlerts();
  const openAlertsCount = alerts?.filter((alert) => alert.status === 'OPEN').length ?? 0;
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommandPaletteOpen(true);
        return;
      }

      if (event.key === 'Escape') {
        if (commandPaletteOpen) {
          setCommandPaletteOpen(false);
        } else if (copilotOpen) {
          setCopilotOpen(false);
        } else if (mobileNavOpen) {
          setMobileNavOpen(false);
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [commandPaletteOpen, copilotOpen, mobileNavOpen]);

  const currentPage = useMemo(() => pageTitles[location.pathname] ?? 'Workspace', [location.pathname]);

  return (
    <div className="min-h-screen bg-[#0B0F17] text-gray-100 flex">
      <Sidebar
        alertCount={openAlertsCount}
        onOpenCopilot={() => setCopilotOpen(true)}
        user={user}
        collapsed={sidebarCollapsed}
        onToggleSidebar={toggleSidebar}
        selectedWarehouseId={selectedWarehouseId}
        mobileOpen={mobileNavOpen}
        onCloseMobile={() => setMobileNavOpen(false)}
      />

      <div
        className={`flex-1 flex flex-col min-h-screen min-w-0 transition-all duration-200 ${sidebarCollapsed ? 'md:ml-20' : 'md:ml-64'}`}
      >
        <Header
          openAlertsCount={openAlertsCount}
          onOpenCopilot={() => setCopilotOpen(true)}
          onOpenAlertsModal={() => navigate('/incidents')}
          user={user}
          currentPage={currentPage}
          connectionState={connectionState}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenMobileNav={() => setMobileNavOpen(true)}
          sidebarCollapsed={sidebarCollapsed}
        />
        <main className="flex-1 min-w-0 mt-16 p-6 md:p-8 overflow-y-auto">{children}</main>
      </div>


      {commandPaletteOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/70 pt-24"
          onClick={() => setCommandPaletteOpen(false)}
        >
          <div
            role="dialog"
            aria-label="Command palette"
            className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#0F172A] shadow-2xl shadow-blue-950/30 p-4"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-[#111827] px-3 py-2 text-sm text-gray-300">
              <span className="text-gray-500">⌘</span>
              <input
                autoFocus
                aria-label="Command palette search"
                placeholder="Search incidents, cameras, zones, reports..."
                className="w-full bg-transparent text-sm text-white placeholder-gray-500 outline-none"
              />
            </div>
            <div className="mt-4 space-y-2 text-sm text-gray-300">
              {[
                ['Open Overview', '/'],
                ['Open Live Streams', '/live'],
                ['Open Incident Board', '/incidents'],
                ['Ask AI Copilot', 'copilot'],
              ].map(([label, route]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => {
                    setCommandPaletteOpen(false);
                    if (route === 'copilot') {
                      setCopilotOpen(true);
                      return;
                    }
                    navigate(route);
                  }}
                  className="flex w-full items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-left hover:border-blue-500/40 hover:bg-blue-500/10"
                >
                  <span>{label}</span>
                  <span className="text-[10px] uppercase tracking-[0.18em] text-gray-500">{route}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <CopilotChatDrawer isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  );
}
