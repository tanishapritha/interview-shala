import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';
import styles from './Badge.module.scss';

export type BadgeTone = 'neutral' | 'accent' | 'bronze' | 'success' | 'warning' | 'danger';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ className, tone = 'neutral', children, ...props }: BadgeProps) {
  return (
    <span className={cn(styles.badge, styles[tone], className)} {...props}>
      {children}
    </span>
  );
}
