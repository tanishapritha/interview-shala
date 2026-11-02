import { cn } from '@/lib/cn';
import styles from './Skeleton.module.scss';

export function Skeleton({
  className,
  width,
  height,
  circle,
}: {
  className?: string;
  width?: string | number;
  height?: string | number;
  circle?: boolean;
}) {
  return (
    <div
      className={cn(styles.skeleton, circle && styles.circle, className)}
      style={{ width, height }}
      aria-hidden
    />
  );
}
