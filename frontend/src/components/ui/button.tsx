import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'outline' | 'link';
type ButtonSize = 'default' | 'sm' | 'lg' | 'icon';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

// Pill button system: every actionable button is fully rounded. `default`
// is the filled brand-blue pill (primary CTA), `secondary` is its ghost
// counterpart (blue border/text, transparent fill) that pairs with it on
// the same row, `outline` is a neutral bordered pill for lower-emphasis
// actions, `ghost` drops the pill entirely for a quiet inline action, and
// `link` is a plain text link (no border, no radius, underline on hover).
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]';

    const variants: Record<ButtonVariant, string> = {
      default: 'rounded-full bg-[#5D87FF] text-white hover:bg-[#3F6AE0]',
      secondary: 'rounded-full border border-[#5D87FF] bg-transparent text-[#2F52D6] hover:bg-[#5D87FF]/10',
      outline: 'rounded-full border border-[#E9EDF2] bg-white text-[#18243A] hover:border-[#CBD5E1] hover:bg-[#F1F5F9]',
      ghost: 'rounded-full text-[#6F7F98] hover:bg-[#F1F5F9] hover:text-[#18243A]',
      link: 'rounded-none text-[#2F52D6] underline-offset-4 hover:underline p-0 h-auto',
    };

    const sizes: Record<ButtonSize, string> = {
      default: 'h-10 px-5 text-sm',
      sm: 'h-8 px-4 text-xs',
      lg: 'h-12 px-6 text-base',
      icon: 'h-10 w-10 p-0',
    };

    const sizeClass = variant === 'link' ? '' : sizes[size];

    return <button ref={ref} className={cn(base, variants[variant], sizeClass, className)} {...props} />;
  },
);

Button.displayName = 'Button';
