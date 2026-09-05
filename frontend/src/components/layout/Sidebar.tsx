import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Boxes,
  Camera,
  Cpu,
  Dna,
  FileCheck,
  LayoutDashboard,
  Layers,
  MapPin,
  PlayCircle,
  Shield,
  Sliders,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  alertCount: number;
  onOpenCopilot: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ alertCount, onOpenCopilot }) => {
  const navLinks = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/live', label: 'Live Streams', icon: Camera },
    { to: '/analysis', label: 'Video Intelligence', icon: PlayCircle },
    { to: '/incidents', label: 'Incident Board', icon: AlertTriangle, badge: alertCount },
    { to: '/evidence', label: 'Evidence Vault', icon: FileCheck },
    { to: '/prevention', label: 'Prevention Studio', icon: Sliders },
    { to: '/digital-twin', label: 'Digital Twin', icon: MapPin },
    { to: '/dna', label: 'Behaviour DNA', icon: Dna },
  ];

  return (
    <aside className="w-64 bg-[#0B0F17] border-r border-white/10 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-white/10 gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 glow-accent">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-wider text-white flex items-center gap-1.5">
            GUARDIAN<span className="text-blue-400">EYE</span>
          </div>
          <div className="text-[10px] font-mono text-gray-400 tracking-tight">
            AI RISK & INTELLIGENCE
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-1.5 text-[11px] font-mono uppercase tracking-wider text-gray-500">
          Command Operations
        </div>
        {navLinks.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </div>
              {link.badge && link.badge > 0 ? (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse">
                  {link.badge}
                </span>
              ) : null}
            </NavLink>
          );
        })}
      </div>

      {/* Grounded Copilot Launcher */}
      <div className="p-4 border-t border-white/10 bg-white/[0.02]">
        <button
          onClick={onOpenCopilot}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-gradient-to-r from-blue-600/30 to-purple-600/30 border border-blue-500/40 text-blue-300 text-xs font-semibold hover:from-blue-600/40 hover:to-purple-600/40 transition-all glow-accent"
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Grounded AI Copilot</span>
        </button>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-gray-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-live" />
          <span>PIPELINE ONLINE</span>
        </div>
        <span className="text-gray-500">v1.0.0</span>
      </div>
    </aside>
  );
};
