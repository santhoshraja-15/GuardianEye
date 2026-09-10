import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class lists the shadcn/ui way: clsx resolves conditionals/arrays,
 * twMerge then drops earlier Tailwind utilities a later one overrides
 * (e.g. a caller's `p-6` beats a component default `p-4`) instead of
 * leaving both in the string. Signature stays compatible with every
 * existing call site (`cn(a, b && c, className)`).
 */
export function cn(...classes: ClassValue[]): string {
  return twMerge(clsx(classes));
}
