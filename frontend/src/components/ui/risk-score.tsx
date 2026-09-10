import { cn } from '../../utils/cn';
import { RiskLevel, designTokens } from '../../styles/design-tokens';

export interface RiskScoreProps {
  value: number;
  level?: RiskLevel;
  className?: string;
}

export function RiskScore({ value, level, className }: RiskScoreProps) {
  const normalizedLevel: RiskLevel = level ?? (value >= 90 ? 'CRITICAL' : value >= 75 ? 'HIGH' : value >= 50 ? 'MEDIUM' : 'LOW');
  const tone = designTokens.semantic[normalizedLevel.toLowerCase() as keyof typeof designTokens.semantic];

  return (
    <div
      className={cn('inline-flex items-baseline gap-2 rounded-full border bg-white px-3 py-2', className)}
      style={{ borderColor: tone.ring }}
    >
      <span className="text-[11px] uppercase tracking-[0.12em] text-[#6F7F98]">Risk</span>
      <span className="text-xl font-semibold" style={{ color: tone.color }}>{value}</span>
      <span className="text-[10px] uppercase tracking-[0.12em] text-[#6F7F98]">/100</span>
    </div>
  );
}
