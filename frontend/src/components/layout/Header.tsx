import React, { useEffect, useState } from 'react';
import {
  Bell,
  CheckCircle,
  Command,
  Menu,
  Search,
  Sparkles,
  Terminal,
  Wifi,
} from 'lucide-react';
import type { AuthUser } from '../../types/auth';

interface HeaderProps {
  openAlertsCount: number;
  onOpenCopilot: () => void;
  onOpenAlertsModal: () => void;
  user: AuthUser | null;
  currentPage: string;
  connectionState?: 'LIVE' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE';
  onOpenCommandPalette: () => void;
  onOpenMobileNav: () => void;
  sidebarCollapsed: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  openAlertsCount,
  onOpenCopilot,
  onOpenAlertsModal,
  user,
  currentPage,
  connectionState = 'LIVE',
  onOpenCommandPalette,
  onOpenMobileNav,
  sidebarCollapsed,
}) => {

  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }) + ' UTC',
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const liveStatusColors = {
    LIVE: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    DEGRADED: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    RECONNECTING: 'bg-sky-500/10 border-sky-500/20 text-sky-400',
    OFFLINE: 'bg-red-500/10 border-red-500/20 text-red-400',
  };

  return (
    <header
      className={`h-16 bg-[#0B0F17]/90 backdrop-blur-md border-b border-white/10 px-4 md:px-8 flex items-center justify-between fixed top-0 right-0 left-0 z-20 transition-all duration-200 ${
        sidebarCollapsed ? 'md:left-20' : 'md:left-64'
      }`}
    >
      <div className="flex items-center gap-4 min-w-0">
        <button
          type="button"
          aria-label="Open navigation"
          onClick={onOpenMobileNav}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition-all md:hidden"
        >
          <Menu className="w-4 h-4" />
        </button>
        <div className="min-w-0">
          <div className="text-[10px] uppercase tracking-[0.18em] text-gray-500">Workspace</div>
          <div className="text-sm font-medium text-white truncate">{currentPage}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <div className="relative hidden md:block w-80 xl:w-96">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="w-full bg-[#111827] border border-white/10 rounded-lg pl-9 pr-10 py-1.5 text-left text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50 transition-colors"
          >
            Search incidents, cameras, alerts, evidence...
          </button>
          <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] font-mono text-gray-400">
            Ctrl+K
          </span>
        </div>

        <div className="hidden lg:flex font-mono text-xs text-gray-400 bg-black/40 border border-white/5 px-3 py-1.5 rounded-lg items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span>{timeStr}</span>
        </div>

        <div
          role="status"
          aria-label={`Connection status: ${connectionState}`}
          className={`flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-lg border text-xs font-mono ${liveStatusColors[connectionState]}`}
        >
          <Wifi className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">{connectionState}</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>ZERO DRIFT</span>
        </div>

        {user ? (
          <div className="hidden sm:flex items-center gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200">
            <span className="font-medium text-white">{user.full_name}</span>
            <span className="text-slate-400">{user.role?.name ?? 'Operator'}</span>
          </div>
        ) : null}

        <button
          type="button"
          aria-label={openAlertsCount > 0 ? `Open alerts (${openAlertsCount} open)` : 'Open alerts'}
          onClick={onOpenAlertsModal}
          className="relative p-2 rounded-lg bg-[#111827] border border-white/10 text-gray-300 hover:text-white hover:border-white/20 transition-all"
        >
          <Bell className="w-4 h-4" />
          {openAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-mono font-bold flex items-center justify-center animate-pulse shadow-lg shadow-red-500/50">
              {openAlertsCount}
            </span>
          )}
        </button>

        <button
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400 text-xs font-medium hover:bg-blue-600/30 transition-all"
        >
          <Command className="w-3.5 h-3.5" />
          <span>Command</span>
        </button>

        <button
          type="button"
          aria-label="Ask Copilot"
          onClick={onOpenCopilot}
          className="flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400 text-xs font-medium hover:bg-blue-600/30 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden sm:inline">Ask Copilot</span>
        </button>
      </div>
    </header>
  );
};

