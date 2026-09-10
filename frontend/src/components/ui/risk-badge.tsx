import { AlertTriangle, ShieldCheck, TriangleAlert } from 'lucide-react';
import { ReactNode } from 'react';
import { cn } from '../../utils/cn';
import { RiskLevel, designTokens } from '../../styles/design-tokens';

export interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  label?: string;
  compact?: boolean;
  className?: string;
  leftIcon?: ReactNode;
}

const riskStyles: Record<RiskLevel, { text: string; border: string; bg: string; icon: typeof ShieldCheck }> = {
  LOW: { text: designTokens.semantic.low.color, border: designTokens.semantic.low.ring, bg: designTokens.semantic.low.bg, icon: ShieldCheck },
  MEDIUM: { text: designTokens.semantic.medium.color, border: designTokens.semantic.medium.ring, bg: designTokens.semantic.medium.bg, icon: TriangleAlert },
  HIGH: { text: designTokens.semantic.high.color, border: designTokens.semantic.high.ring, bg: designTokens.semantic.high.bg, icon: AlertTriangle },
  CRITICAL: { text: designTokens.semantic.critical.color, border: designTokens.semantic.critical.ring, bg: designTokens.semantic.critical.bg, icon: AlertTriangle },
};

export function RiskBadge({ level, score, label, compact = false, className, leftIcon }: RiskBadgeProps) {
  const style = riskStyles[level];
  const Icon = style.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-2.5 py-1 font-medium',
        compact ? 'text-[10px]' : 'text-[11px]',
        className,
      )}
      style={{
        color: style.text,
        backgroundColor: style.bg,
        borderColor: style.border,
      }}
    >
      {leftIcon ?? <Icon size={compact ? 12 : 14} />}
      <span className="uppercase tracking-[0.12em]">
        {label ?? designTokens.semantic[level.toLowerCase() as keyof typeof designTokens.semantic].label}
      </span>
      {typeof score === 'number' && (
        <span className="text-[10px] opacity-80">{score}</span>
      )}
    </span>
  );
}
