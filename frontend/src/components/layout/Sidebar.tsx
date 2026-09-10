import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  AlertTriangle,
  Camera,
  ChevronLeft,
  ChevronRight,
  Crosshair,
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
    { to: '/calibration', label: 'Camera Calibration', icon: Crosshair },
    { to: '/dna', label: 'Behaviour DNA', icon: Dna },
    { to: '/human-review', label: 'Human Review', icon: Shield },
  ];

  return (
    <>
      {mobileOpen && (
        <div
          className="ge-mobile-overlay fixed inset-0 z-30 bg-[#18243A]/35 md:hidden"
          aria-hidden="true"
          onClick={onCloseMobile}
        />
      )}
      <aside
        className={`w-64 ${collapsed ? 'md:w-20' : 'md:w-64'} ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 bg-white border-r border-[#E9EDF2] flex flex-col h-screen fixed left-0 top-0 z-40 select-none transition-all duration-200`}
      >
        <div className="h-16 flex items-center justify-between px-3 border-b border-[#E9EDF2] gap-3">
          <div className={`flex items-center gap-3 ${collapsed ? 'md:justify-center md:w-full' : ''}`}>
            <img
              src="/images/logo/logo_ge_icon.png"
              alt="GuardianEye"
              className="h-9 w-9 shrink-0 object-contain"
            />
            {!collapsed && (
              <div>
                <div className="font-[family-name:var(--font-brand)] font-semibold text-lg leading-none text-[#18243A] flex items-center gap-1">
                  Guardian<span className="text-[#2F52D6]">Eye</span>
                </div>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[#9DAFC5] mt-1">
                  AI Risk &amp; Intelligence
                </div>
              </div>
            )}
          </div>
          <button
            type="button"
            aria-label="Close navigation"
            onClick={onCloseMobile}
            className="flex h-7 w-7 items-center justify-center rounded-full border border-[#E9EDF2] bg-white text-[#6F7F98] hover:text-[#18243A] hover:border-[#CBD5E1] transition-all md:hidden"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={onToggleSidebar}
            className="hidden md:flex h-7 w-7 items-center justify-center rounded-full border border-[#E9EDF2] bg-white text-[#6F7F98] hover:text-[#18243A] hover:border-[#CBD5E1] transition-all"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {!collapsed && (
          <div className="px-3 py-3 border-b border-[#E9EDF2]">
            <div className="rounded-2xl border border-[#E9EDF2] bg-[#F1F5F9] px-3 py-2">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.14em] text-[#6F7F98]">
                <MapPin className="w-3.5 h-3.5" />
                Warehouse
              </div>
              <div className="mt-1.5 text-sm font-medium text-[#18243A]">{selectedWarehouseId ?? 'Primary'}</div>
            </div>
          </div>
        )}

        <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {!collapsed && (
            <div className="px-3 py-1.5 text-[11px] uppercase tracking-wider text-[#9DAFC5]">
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
                  `flex items-center justify-between px-3 py-2.5 rounded-full text-[13px] font-medium transition-all ${
                    collapsed ? 'justify-center' : ''
                  } ${
                    isActive
                      ? 'bg-[#5D87FF] text-white'
                      : 'text-[#6F7F98] hover:text-[#18243A] hover:bg-[#F1F5F9]'
                  }`
                }
              >
                <div className={`flex items-center ${collapsed ? 'justify-center w-full' : 'gap-3'}`}>
                  <Icon className="w-4 h-4" />
                  {!collapsed && <span>{link.label}</span>}
                </div>
                {!collapsed && link.badge && link.badge > 0 ? (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#EAF0FF] text-[#2F52D6]">
                    {link.badge}
                  </span>
                ) : null}
              </NavLink>
            );
          })}
        </div>

        <div className="p-4 border-t border-[#E9EDF2]">
          <button
            onClick={onOpenCopilot}
            className={`w-full flex items-center justify-center gap-2 rounded-full bg-[#5D87FF] text-white text-xs font-semibold hover:bg-[#3F6AE0] transition-all ${collapsed ? 'px-2 py-2' : 'px-3 py-2.5'}`}
          >
            <Sparkles className="w-4 h-4" />
            {!collapsed && <span>Grounded AI Copilot</span>}
          </button>
        </div>

        <div className={`p-4 border-t border-[#E9EDF2] flex items-center ${collapsed ? 'justify-center' : 'justify-between'} text-[11px] text-[#6F7F98]`}>
          {!collapsed ? (
            <>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#15803d] pulse-live" />
                <span>Pipeline online</span>
              </div>
              <span className="text-[#9DAFC5]">v1.0.0</span>
            </>
          ) : (
            <span className="w-2 h-2 rounded-full bg-[#15803d] pulse-live" />
          )}
        </div>
      </aside>
    </>
  );
};
