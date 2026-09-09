import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, style, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('rounded-xl p-4', className)}
      style={{
        background: 'var(--card-bg, rgba(15, 23, 42, 0.8))',
        border: '1px solid var(--card-border, rgba(255, 255, 255, 0.08))',
        boxShadow: 'var(--card-shadow, 0 4px 20px rgba(0,0,0,0.4))',
        ...style,
      }}
      {...props}
    />
  ),
);

Card.displayName = 'Card';
