export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

// ─── Design system — rounded admin blue ─────────────────────────────────
// A light, near-white admin canvas with AdminMart/Modernize-style blue as
// the single brand accent, set in Plus Jakarta Sans (Tokotype) throughout,
// falling back to Noto Sans.
//
// Risk-severity colors (low/medium/high/critical) are the one deliberate
// exception to the accent-blue-only palette: they encode functional safety
// information (alert/incident severity), not decoration, so they keep the
// standard green/amber/orange/red convention — retuned to darker, WCAG
// AA-passing shades against this theme's white/mist surfaces.
export const designTokens = {
  colors: {
    background: '#ffffff',
    navigation: '#ffffff',
    panel: '#F1F5F9',
    panelElevated: '#ffffff',
    border: '#E9EDF2',
    text: '#18243A',
    textMuted: '#6F7F98',
    accent: '#5D87FF',
    accentInk: '#2F52D6',
    low: '#15803d',
    medium: '#92400e',
    high: '#9a3412',
    critical: '#b91c1c',
    white: '#ffffff',
    shadow: 'rgba(4, 23, 43, 0.08)',
  },
  typography: {
    fontFamily: '"Plus Jakarta Sans", "Noto Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    display: '"Plus Jakarta Sans", "Noto Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    mono: '"Plus Jakarta Sans", "SFMono-Regular", monospace',
    heading: {
      xs: '0.7rem',
      sm: '0.875rem',
      md: '1rem',
      lg: '1.25rem',
      xl: '1.625rem',
      xxl: '2.25rem',
    },
    weight: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    tracking: {
      tight: '-0.04em',
      normal: '0',
      wide: '0.12em',
    },
  },
  spacing: {
    xxs: 4,
    xs: 8,
    sm: 12,
    md: 16,
    lg: 20,
    xl: 24,
    xxl: 32,
  },
  radius: {
    sm: 16,
    md: 16,
    lg: 20,
    xl: 24,
    full: 9999,
  },
  shadows: {
    sm: '0 0 0 1px rgba(4,23,43,0.05), 0 4px 24px rgba(0,0,0,0.06)',
    md: '0 0 0 1px rgba(4,23,43,0.05), 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)',
    lg: '0 0 0 1px rgba(4,23,43,0.05), 0 20px 60px rgba(0,0,0,0.12)',
  },
  transitions: {
    fast: '150ms ease',
    medium: '220ms ease',
    slow: '320ms ease',
  },
  zIndex: {
    base: 0,
    dropdown: 10,
    sticky: 20,
    modal: 40,
    overlay: 50,
  },
  breakpoints: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
  },
  semantic: {
    low: {
      label: 'LOW',
      color: '#15803d',
      bg: 'rgba(21, 128, 61, 0.1)',
      ring: 'rgba(21, 128, 61, 0.3)',
    },
    medium: {
      label: 'MEDIUM',
      color: '#92400e',
      bg: 'rgba(146, 64, 14, 0.1)',
      ring: 'rgba(146, 64, 14, 0.3)',
    },
    high: {
      label: 'HIGH',
      color: '#9a3412',
      bg: 'rgba(154, 52, 18, 0.1)',
      ring: 'rgba(154, 52, 18, 0.3)',
    },
    critical: {
      label: 'CRITICAL',
      color: '#b91c1c',
      bg: 'rgba(185, 28, 28, 0.1)',
      ring: 'rgba(185, 28, 28, 0.3)',
    },
  },
} as const;

export const riskOrder: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const riskColorMap: Record<RiskLevel, string> = {
  LOW: designTokens.colors.low,
  MEDIUM: designTokens.colors.medium,
  HIGH: designTokens.colors.high,
  CRITICAL: designTokens.colors.critical,
};
