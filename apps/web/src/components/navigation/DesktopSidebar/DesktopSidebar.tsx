import { NavLink } from 'react-router-dom';
import { Home, BookOpen, Mic, LineChart, User } from 'lucide-react';
import { cn } from '@/lib/cn';
import styles from './DesktopSidebar.module.scss';

const items = [
  { to: '/app', label: 'Home', icon: Home, end: true },
  { to: '/app/prepare', label: 'Prepare', icon: BookOpen },
  { to: '/app/practice', label: 'Practice', icon: Mic },
  { to: '/app/progress', label: 'Progress', icon: LineChart },
  { to: '/app/profile', label: 'Profile', icon: User },
] as const;

export function DesktopSidebar() {
  return (
    <aside className={styles.sidebar}>
      <NavLink to="/" className={styles.brand}>
        <img src="/favicon.svg" alt="" className={styles.logo} width={36} height={36} />
        <span className={styles.name}>Interview Shala</span>
      </NavLink>
      <nav className={styles.nav} aria-label="Primary">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={Boolean(end)}
            className={({ isActive }) => cn(styles.link, isActive && styles.active)}
          >
            <Icon size={18} aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>
      <p className={styles.footer}>Your next interview shouldn't be a surprise.</p>
    </aside>
  );
}
