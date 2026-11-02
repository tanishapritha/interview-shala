import * as RadixToast from '@radix-ui/react-toast';
import { create } from 'zustand';
import styles from './Toast.module.scss';

type ToastItem = {
  id: string;
  title: string;
  description?: string;
  tone?: 'default' | 'success' | 'danger';
};

type ToastStore = {
  items: ToastItem[];
  push: (item: Omit<ToastItem, 'id'>) => void;
  dismiss: (id: string) => void;
};

export const useToastStore = create<ToastStore>((set) => ({
  items: [],
  push: (item) =>
    set((state) => ({
      items: [...state.items, { ...item, id: crypto.randomUUID() }],
    })),
  dismiss: (id) => set((state) => ({ items: state.items.filter((t) => t.id !== id) })),
}));

export function toast(item: Omit<ToastItem, 'id'>) {
  useToastStore.getState().push(item);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const items = useToastStore((s) => s.items);
  const dismiss = useToastStore((s) => s.dismiss);

  return (
    <RadixToast.Provider swipeDirection="right" duration={4000}>
      {children}
      {items.map((item) => (
        <RadixToast.Root
          key={item.id}
          className={`${styles.root} ${item.tone === 'success' ? styles.success : ''} ${item.tone === 'danger' ? styles.danger : ''}`}
          onOpenChange={(open) => {
            if (!open) dismiss(item.id);
          }}
        >
          <RadixToast.Title className={styles.title}>{item.title}</RadixToast.Title>
          {item.description ? (
            <RadixToast.Description className={styles.description}>
              {item.description}
            </RadixToast.Description>
          ) : null}
        </RadixToast.Root>
      ))}
      <RadixToast.Viewport className={styles.viewport} />
    </RadixToast.Provider>
  );
}
