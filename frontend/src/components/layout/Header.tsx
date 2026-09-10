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
    LIVE: 'bg-[rgba(21,128,61,0.08)] border-[rgba(21,128,61,0.25)] text-[#15803d]',
    DEGRADED: 'bg-[rgba(146,64,14,0.08)] border-[rgba(146,64,14,0.25)] text-[#92400e]',
    RECONNECTING: 'bg-[rgba(47,82,214,0.08)] border-[rgba(47,82,214,0.25)] text-[#2F52D6]',
    OFFLINE: 'bg-[rgba(185,28,28,0.08)] border-[rgba(185,28,28,0.25)] text-[#b91c1c]',
  };

  return (
    <header
      className={`h-16 bg-white/90 backdrop-blur-md border-b border-[#E9EDF2] px-4 md:px-8 flex items-center justify-between fixed top-0 right-0 left-0 z-20 transition-all duration-200 ${
        sidebarCollapsed ? 'md:left-20' : 'md:left-64'
      }`}
    >
      <div className="flex items-center gap-4 shrink-0">
        <button
          type="button"
          aria-label="Open navigation"
          onClick={onOpenMobileNav}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[#E9EDF2] bg-white text-[#6F7F98] hover:text-[#18243A] hover:border-[#CBD5E1] transition-all md:hidden"
        >
          <Menu className="w-4 h-4" />
        </button>
        <div>
          <div className="text-[10px] uppercase tracking-[0.14em] text-[#9DAFC5] whitespace-nowrap">Workspace</div>
          <div className="text-sm font-medium text-[#18243A] whitespace-nowrap font-[family-name:var(--font-signifier)]">{currentPage}</div>
        </div>
      </div>

      {/* Middle region is the one flexible element in this row (min-w-0
          lets it shrink below its content size) — every other header
          element is shrink-0, so the search field is what gives up width
          first on a narrow viewport instead of the page title truncating
          into unreadable fragments. */}
      <div className="hidden md:flex flex-1 min-w-0 justify-end px-3">
        <div className="relative w-full min-w-[160px] max-w-96">
          <Search className="w-4 h-4 text-[#9DAFC5] absolute left-3 top-1/2 -translate-y-1/2" />
          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="w-full bg-[#F1F5F9] border border-[#E9EDF2] rounded-full pl-9 pr-14 py-1.5 text-left text-xs text-[#6F7F98] hover:border-[#CBD5E1] focus:outline-none transition-colors truncate"
          >
            Search incidents, cameras, alerts, evidence...
          </button>
          <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full border border-[#E9EDF2] bg-white px-1.5 py-0.5 text-[10px] text-[#9DAFC5]">
            Ctrl+K
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        <div className="hidden lg:flex shrink-0 text-xs text-[#6F7F98] bg-[#F1F5F9] border border-[#E9EDF2] px-3 py-1.5 rounded-full items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-[#2F52D6]" />
          <span>{timeStr}</span>
        </div>

        <div
          role="status"
          aria-label={`Connection status: ${connectionState}`}
          className={`flex shrink-0 items-center gap-2 px-2 sm:px-3 py-1.5 rounded-full border text-xs ${liveStatusColors[connectionState]}`}
        >
          <Wifi className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">{connectionState}</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[rgba(21,128,61,0.08)] border border-[rgba(21,128,61,0.25)] text-[#15803d] text-xs">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Zero drift</span>
        </div>

        {user ? (
          <div className="hidden sm:flex items-center gap-3 rounded-full border border-[#E9EDF2] bg-white px-3 py-1.5 text-xs text-[#18243A]">
            <span className="font-medium">{user.full_name}</span>
            <span className="text-[#9DAFC5]">{user.role?.name ?? 'Operator'}</span>
          </div>
        ) : null}

        <button
          type="button"
          aria-label={openAlertsCount > 0 ? `Open alerts (${openAlertsCount} open)` : 'Open alerts'}
          onClick={onOpenAlertsModal}
          className="relative p-2 rounded-full bg-white border border-[#E9EDF2] text-[#6F7F98] hover:text-[#18243A] hover:border-[#CBD5E1] transition-all"
        >
          <Bell className="w-4 h-4" />
          {openAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#b91c1c] text-white text-[10px] font-bold flex items-center justify-center">
              {openAlertsCount}
            </span>
          )}
        </button>

        <button
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#5D87FF] text-[#2F52D6] text-xs font-medium hover:bg-[#5D87FF]/10 transition-all"
        >
          <Command className="w-3.5 h-3.5" />
          <span>Command</span>
        </button>

        <button
          type="button"
          aria-label="Ask Copilot"
          onClick={onOpenCopilot}
          className="flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-full bg-[#5D87FF] text-white text-xs font-medium hover:bg-[#3F6AE0] transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Ask Copilot</span>
        </button>
      </div>
    </header>
  );
};
