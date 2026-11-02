import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/cn';
import styles from './MobileHeader.module.scss';

export function MobileHeader({
  actions,
  bordered = true,
  brandHref = '/',
}: {
  actions?: ReactNode;
  bordered?: boolean;
  brandHref?: string;
}) {
  return (
    <header className={cn(styles.header, bordered && styles.bordered)}>
      <div className={styles.inner}>
        <Link to={brandHref} className={styles.brand}>
          <img src="/favicon.svg" alt="" className={styles.logo} width={32} height={32} />
          <span className={styles.name}>Interview Shala</span>
        </Link>
        {actions ? <div className={styles.actions}>{actions}</div> : null}
      </div>
    </header>
  );
}
