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
        return 'bg-[rgba(185,28,28,0.1)] text-[#b91c1c] border-[rgba(185,28,28,0.3)] glow-critical';
      case 'HIGH':
        return 'bg-[rgba(154,52,18,0.1)] text-[#9a3412] border-[rgba(154,52,18,0.3)] glow-high';
      case 'MEDIUM':
        return 'bg-[rgba(146,64,14,0.1)] text-[#92400e] border-[rgba(146,64,14,0.3)] glow-medium';
      case 'LOW':
        return 'bg-[rgba(21,128,61,0.1)] text-[#15803d] border-[rgba(21,128,61,0.3)] glow-low';
      case 'OPEN':
      case 'DETECTED':
        return 'bg-[rgba(47,82,214,0.08)] text-[#2F52D6] border-[rgba(47,82,214,0.25)]';
      case 'ACKNOWLEDGED':
      case 'CONFIRMED':
      case 'RESOLVED':
        return 'bg-[#F1F5F9] text-[#18243A] border-[#E9EDF2]';
      case 'UNDER_REVIEW':
      case 'ALERTED':
      case 'REJECTED':
        return 'bg-[rgba(47,82,214,0.08)] text-[#2F52D6] border-[rgba(47,82,214,0.25)]';
      case 'ACTION_TAKEN':
        return 'bg-[rgba(21,128,61,0.1)] text-[#15803d] border-[rgba(21,128,61,0.3)]';
      default:
        return 'bg-[#F1F5F9] text-[#6F7F98] border-[#E9EDF2]';
    }
  };

  const pad = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center font-semibold tracking-wide rounded-full border ${pad} ${getStyle()}`}
    >
      {norm}
    </span>
  );
};
