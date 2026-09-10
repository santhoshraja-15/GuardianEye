import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

type CardVariant = 'neutral' | 'elevated' | 'accent';

type CardProps = HTMLAttributes<HTMLDivElement> & {
  variant?: CardVariant;
};

// Card surfaces:
//  - neutral:  pale surface fill, 24px radius, no shadow — the default workhorse
//  - elevated: white "floating" card, subtle shadow
//  - accent:   soft brand-blue callout — use sparingly, one per page
export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'neutral', ...props }, ref) => {
    const variants: Record<CardVariant, string> = {
      neutral: 'bg-[#F1F5F9] rounded-3xl',
      elevated: 'bg-white rounded-[20px] shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_25px_-5px_rgba(0,0,0,0.1),0_8px_10px_-6px_rgba(0,0,0,0.1)]',
      accent: 'bg-[#EAF0FF] text-[#2F52D6] rounded-3xl',
    };

    return <div ref={ref} className={cn('p-5', variants[variant], className)} {...props} />;
  },
);

Card.displayName = 'Card';
