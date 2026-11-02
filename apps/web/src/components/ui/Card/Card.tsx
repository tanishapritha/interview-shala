import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';
import styles from './Card.module.scss';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  compact?: boolean;
  interactive?: boolean;
  as?: 'div' | 'article' | 'section';
}

export function Card({
  className,
  compact,
  interactive,
  as: Comp = 'div',
  children,
  ...props
}: CardProps) {
  return (
    <Comp
      className={cn(styles.card, compact && styles.compact, interactive && styles.interactive, className)}
      {...props}
    >
      {children}
    </Comp>
  );
}

export function CardHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow?: string;
  title: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={styles.header}>
      <div>
        {eyebrow ? <p className={styles.eyebrow}>{eyebrow}</p> : null}
        <h3 className={styles.title}>{title}</h3>
      </div>
      {action}
    </div>
  );
}
