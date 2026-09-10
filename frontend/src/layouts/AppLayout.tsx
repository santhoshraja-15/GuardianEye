import { ReactNode, useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
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
  '/calibration': 'Camera Calibration',
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
    <div className="ge-layout-root min-h-screen bg-white text-[#18243A] flex">
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
        <main className="flex-1 min-w-0 mt-16 p-6 md:p-8 overflow-y-auto">
          {/* Page-entry transition: quiet fade + 8px settle, no exit animation
              (the incoming page painting immediately reads as more responsive
              than waiting through an outgoing fade on a data-heavy dashboard). */}
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.28, ease: [0.4, 0, 0.2, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Not wrapped in AnimatePresence: only the mount plays a motion
          transition (initial → animate). Closing removes the dialog from
          the DOM in the same tick as the state update — Escape/backdrop
          dismissal stays synchronous instead of waiting out an exit
          animation, matching the rest of the app's keyboard/pointer
          dismissal contract. */}
      {commandPaletteOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center bg-[#18243A]/45 pt-24"
          onClick={() => setCommandPaletteOpen(false)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
        >
          <motion.div
            role="dialog"
            aria-label="Command palette"
            className="w-full max-w-2xl rounded-3xl border border-[#E9EDF2] bg-white shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_60px_rgba(0,0,0,0.12)] p-4"
            onClick={(event) => event.stopPropagation()}
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
          >
            <div className="flex items-center gap-3 rounded-2xl border border-[#E9EDF2] bg-[#F1F5F9] px-3 py-2 text-sm text-[#18243A]">
              <span className="text-[#9DAFC5]">⌘</span>
              <input
                autoFocus
                aria-label="Command palette search"
                placeholder="Search incidents, cameras, zones, reports..."
                className="w-full bg-transparent text-sm text-[#18243A] placeholder-[#9DAFC5] outline-none"
              />
            </div>
            <div className="mt-4 space-y-2 text-sm text-[#18243A]">
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
                  className="flex w-full items-center justify-between rounded-2xl border border-[#E9EDF2] bg-white px-3 py-2 text-left transition-colors hover:border-[rgba(47,82,214,0.3)] hover:bg-[rgba(234,240,255,0.35)]"
                >
                  <span>{label}</span>
                  <span className="text-[10px] uppercase tracking-[0.18em] text-[#9DAFC5]">{route}</span>
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}

      <CopilotChatDrawer isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  );
}
