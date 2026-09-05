import React from 'react';
import { SeverityLevel } from '../../types';

interface StatusBadgeProps {
  level: SeverityLevel | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ level, size = 'sm' }) => {
  const norm = level.toUpperCase();

  const getStyle = () => {
    switch (norm) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/40 glow-critical';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40 glow-high';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40 glow-medium';
      case 'LOW':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 glow-low';
      case 'RESOLVED':
      case 'CONFIRMED':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
      case 'UNDER_REVIEW':
      case 'ALERTED':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/40';
    }
  };

  const pad = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center font-mono font-bold rounded-md border ${pad} ${getStyle()}`}
    >
      {norm}
    </span>
  );
};
