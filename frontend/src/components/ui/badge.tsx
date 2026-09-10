import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

// Tag / Category Label — intentionally ghost-like: no background,
// no border, just a typographic marker that groups without visual weight.
export const Badge = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('inline-flex items-center text-[14px] font-normal tracking-wide text-[#9DAFC5]', className)}
      {...props}
    />
  ),
);

Badge.displayName = 'Badge';
