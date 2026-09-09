import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useAppStore } from '../../stores/app-store';

/**
 * Theme toggle button — renders a Sun icon in dark mode (click → go light)
 * and a Moon icon in light mode (click → go dark).
 *
 * Styled to match the existing Header chrome so it feels native, not bolted on.
 */
export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useAppStore();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      onClick={toggleTheme}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className={`
        flex items-center justify-center w-8 h-8 rounded-lg border transition-all duration-200
        ${isDark
          ? 'bg-white/5 border-white/10 text-amber-300 hover:bg-white/10 hover:border-white/20 hover:text-amber-200'
          : 'bg-white/10 border-white/20 text-blue-200 hover:bg-white/15 hover:border-white/30 hover:text-white'
        }
      `}
    >
      {isDark
        ? <Sun className="w-4 h-4" aria-hidden="true" />
        : <Moon className="w-4 h-4" aria-hidden="true" />
      }
    </button>
  );
};
