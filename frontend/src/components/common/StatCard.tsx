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
        return 'border-red-500/30 text-red-400 bg-red-500/10 glow-critical';
      case 'warning':
        return 'border-amber-500/30 text-amber-400 bg-amber-500/10 glow-medium';
      case 'success':
        return 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10 glow-low';
      case 'blue':
        return 'border-blue-500/30 text-blue-400 bg-blue-500/10 glow-accent';
      default:
        return 'border-white/10 text-gray-400 bg-white/5';
    }
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-5 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-gray-400">
            {title}
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight text-white mt-1">
            {value}
          </div>
          {subtitle && (
            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1.5">
              {subtitle}
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg border ${getGlow()}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <span className="text-gray-400">Trend (vs prev 24h)</span>
          <span
            className={`font-mono font-medium ${
              trendDirection === 'down'
                ? 'text-emerald-400'
                : trendDirection === 'up'
                ? 'text-red-400'
                : 'text-gray-300'
            }`}
          >
            {trend}
          </span>
        </div>
      )}
    </div>
  );
};
