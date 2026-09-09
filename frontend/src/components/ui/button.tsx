import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'outline';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50';

    const variants: Record<ButtonVariant, string> = {
      default: 'bg-blue-600 text-white hover:bg-blue-500',
      secondary:
        'border text-sm font-medium transition-colors'
        + ' [background:var(--bg-secondary,#1e293b)] [border-color:var(--border-color,rgba(255,255,255,0.1))]'
        + ' [color:var(--text-primary,#e2e8f0)] hover:[background:var(--bg-primary,#0b0f17)]',
      outline:
        'border bg-transparent text-sm font-medium transition-colors'
        + ' [border-color:var(--border-color,rgba(255,255,255,0.1))]'
        + ' [color:var(--text-secondary,#9ca3af)] hover:[background:var(--bg-secondary,#1e293b)]',
      ghost:
        '[color:var(--text-secondary,#9ca3af)] hover:[background:var(--bg-secondary,#1e293b)] transition-colors',
    };

    return <button ref={ref} className={cn(base, variants[variant], className)} {...props} />;
  },
);

Button.displayName = 'Button';
