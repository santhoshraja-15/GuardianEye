import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  variant?: 'default' | 'critical' | 'warning' | 'success' | 'blue';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendDirection = 'neutral',
  variant = 'default',
}) => {
  const getGlow = () => {
    switch (variant) {
      case 'critical':
        return 'border-[rgba(185,28,28,0.3)] text-[#b91c1c] bg-[rgba(185,28,28,0.08)] glow-critical';
      case 'warning':
        return 'border-[rgba(146,64,14,0.3)] text-[#92400e] bg-[rgba(146,64,14,0.08)] glow-medium';
      case 'success':
        return 'border-[rgba(21,128,61,0.3)] text-[#15803d] bg-[rgba(21,128,61,0.08)] glow-low';
      case 'blue':
        return 'border-[rgba(47,82,214,0.3)] text-[#2F52D6] bg-[rgba(47,82,214,0.08)] glow-accent';
      default:
        return 'border-[#E9EDF2] text-[#6F7F98] bg-[#F1F5F9]';
    }
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-[20px] p-5 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-[#6F7F98]">
            {title}
          </div>
          <div className="text-2xl font-medium tracking-tight text-[#18243A] mt-1">
            {value}
          </div>
          {subtitle && (
            <div className="text-xs text-[#6F7F98] mt-1 flex items-center gap-1.5">
              {subtitle}
            </div>
          )}
        </div>
        <div className={`p-3 rounded-2xl border ${getGlow()}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-[#E9EDF2] flex items-center justify-between text-xs">
          <span className="text-[#6F7F98]">Trend (vs prev 24h)</span>
          <span
            className={`font-medium ${
              trendDirection === 'down'
                ? 'text-[#15803d]'
                : trendDirection === 'up'
                ? 'text-[#b91c1c]'
                : 'text-[#334155]'
            }`}
          >
            {trend}
          </span>
        </div>
      )}
    </div>
  );
};
