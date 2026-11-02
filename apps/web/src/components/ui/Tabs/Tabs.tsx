import * as RadixTabs from '@radix-ui/react-tabs';
import type { ReactNode } from 'react';
import styles from './Tabs.module.scss';

export function Tabs({
  value,
  onValueChange,
  defaultValue,
  children,
}: {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <RadixTabs.Root value={value} defaultValue={defaultValue} onValueChange={onValueChange}>
      {children}
    </RadixTabs.Root>
  );
}

export function TabsList({ items }: { items: { value: string; label: string }[] }) {
  return (
    <RadixTabs.List className={styles.list} aria-label="Sections">
      {items.map((item) => (
        <RadixTabs.Trigger key={item.value} value={item.value} className={styles.trigger}>
          {item.label}
        </RadixTabs.Trigger>
      ))}
    </RadixTabs.List>
  );
}

export function TabsContent({ value, children }: { value: string; children: ReactNode }) {
  return (
    <RadixTabs.Content value={value} className={styles.content}>
      {children}
    </RadixTabs.Content>
  );
}
