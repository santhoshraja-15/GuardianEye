import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  AlertTriangle,
  Camera,
  ChevronLeft,
  ChevronRight,
  Dna,
  FileCheck,
  LayoutDashboard,
  MapPin,
  PlayCircle,
  Shield,
  Sliders,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import type { AuthUser } from '../../types/auth';

interface SidebarProps {
  alertCount: number;
  onOpenCopilot: () => void;
  user: AuthUser | null;
  collapsed: boolean;
  onToggleSidebar: () => void;
  selectedWarehouseId?: string | null;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  alertCount,
  onOpenCopilot,
  user,
  collapsed,
  onToggleSidebar,
  selectedWarehouseId,
  mobileOpen,
  onCloseMobile,
}) => {
  const navLinks = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/live', label: 'Live Streams', icon: Camera },
    { to: '/analysis', label: 'Video Intelligence', icon: PlayCircle },
    { to: '/analytics', label: 'Analytics', icon: TrendingUp },
    { to: '/incidents', label: 'Incident Board', icon: AlertTriangle, badge: alertCount },
    { to: '/evidence', label: 'Evidence Vault', icon: FileCheck },
    { to: '/prevention', label: 'Prevention Studio', icon: Sliders },
    { to: '/digital-twin', label: 'Digital Twin', icon: MapPin },
    { to: '/dna', label: 'Behaviour DNA', icon: Dna },
    { to: '/human-review', label: 'Human Review', icon: Shield },
  ];


  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/70 md:hidden"
          aria-hidden="true"
          onClick={onCloseMobile}
        />
      )}
      <aside
        className={`w-64 ${collapsed ? 'md:w-20' : 'md:w-64'} ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 bg-[#0B0F17] border-r border-white/10 flex flex-col h-screen fixed left-0 top-0 z-40 select-none transition-all duration-200`}
      >
      <div className="h-16 flex items-center justify-between px-3 border-b border-white/10 gap-3">
        <div className={`flex items-center gap-3 ${collapsed ? 'md:justify-center md:w-full' : ''}`}>
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 glow-accent shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div>
              <div className="text-sm font-bold tracking-wider text-white flex items-center gap-1.5">
                GUARDIAN<span className="text-blue-400">EYE</span>
              </div>
              <div className="text-[10px] font-mono text-gray-400 tracking-tight">
                AI RISK & INTELLIGENCE
              </div>
            </div>
          )}
        </div>
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onCloseMobile}
          className="flex h-7 w-7 items-center justify-center rounded-md border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition-all md:hidden"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
          type="button"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          onClick={onToggleSidebar}
          className="hidden md:flex h-7 w-7 items-center justify-center rounded-md border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition-all"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {!collapsed && (
        <div className="px-3 py-3 border-b border-white/10">
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 px-3 py-2">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">
              <MapPin className="w-3.5 h-3.5" />
              Warehouse
            </div>
            <div className="mt-2 text-sm font-semibold text-white">{selectedWarehouseId ?? 'Primary'}</div>
          </div>
        </div>
      )}

      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {!collapsed && (
          <div className="px-3 py-1.5 text-[11px] font-mono uppercase tracking-wider text-gray-500">
            Command Operations
          </div>
        )}
        {navLinks.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              title={collapsed ? link.label : undefined}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  collapsed ? 'justify-center' : ''
                } ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`
              }
            >
              <div className={`flex items-center ${collapsed ? 'justify-center w-full' : 'gap-3'}`}>
                <Icon className="w-4 h-4" />
                {!collapsed && <span>{link.label}</span>}
              </div>
              {!collapsed && link.badge && link.badge > 0 ? (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse">
                  {link.badge}
                </span>
              ) : null}
            </NavLink>
          );
        })}
      </div>

      <div className="p-4 border-t border-white/10 bg-white/[0.02]">
        <button
          onClick={onOpenCopilot}
          className={`w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-600/30 to-purple-600/30 border border-blue-500/40 text-blue-300 text-xs font-semibold hover:from-blue-600/40 hover:to-purple-600/40 transition-all glow-accent ${collapsed ? 'px-2 py-2' : 'px-3 py-2.5'}`}
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          {!collapsed && <span>Grounded AI Copilot</span>}
        </button>
      </div>

      <div className={`p-4 border-t border-white/10 flex items-center ${collapsed ? 'justify-center' : 'justify-between'} text-[11px] font-mono text-gray-400`}>
        {!collapsed ? (
          <>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-live" />
              <span>PIPELINE ONLINE</span>
            </div>
            <span className="text-gray-500">v1.0.0</span>
          </>
        ) : (
          <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-live" />
        )}
      </div>
      </aside>
    </>
  );
};
