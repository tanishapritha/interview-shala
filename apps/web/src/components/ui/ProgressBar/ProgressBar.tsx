import { cn } from '@/lib/cn';
import styles from './ProgressBar.module.scss';

export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: 'md' | 'lg';
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = true,
  size = 'md',
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(value, max));
  const percent = max === 0 ? 0 : Math.round((clamped / max) * 100);

  return (
    <div className={cn(styles.wrap, size === 'lg' && styles.lg, className)}>
      {(label || showValue) && (
        <div className={styles.meta}>
          {label ? <span className={styles.label}>{label}</span> : <span />}
          {showValue ? (
            <span className={styles.value} aria-hidden>
              {percent}%
            </span>
          ) : null}
        </div>
      )}
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label ?? 'Progress'}
      >
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
