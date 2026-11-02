import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';
import styles from './Input.module.scss';

type SharedProps = {
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  optional?: boolean | undefined;
  className?: string | undefined;
  id?: string | undefined;
};

export type InputProps = SharedProps &
  Omit<InputHTMLAttributes<HTMLInputElement>, 'className' | 'id'> & {
    as?: 'input';
  };

export type TextAreaProps = SharedProps &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className' | 'id'> & {
    as: 'textarea';
  };

function FieldShell({
  label,
  optional,
  hint,
  error,
  id,
  children,
  className,
}: SharedProps & { children: React.ReactNode }) {
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;

  return (
    <div className={cn(styles.field, className)}>
      <label className={styles.label} htmlFor={id}>
        {label}
        {optional ? <span className={styles.optional}>(optional)</span> : null}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className={styles.hint}>
          {hint}
        </p>
      ) : null}
      {/* describedBy wired via clone — consumers pass aria-describedby */}
      <span className="sr-only" data-describedby={describedBy} />
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, optional, className, id, as: _as, ...props },
  ref,
) {
  const inputId = id ?? props.name ?? label.toLowerCase().replace(/\\s+/g, '-');
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <FieldShell
      label={label}
      optional={optional}
      hint={hint}
      error={error}
      id={inputId}
      className={className}
    >
      <input
        ref={ref}
        id={inputId}
        className={styles.control}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        {...props}
      />
    </FieldShell>
  );
});

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, hint, error, optional, className, id, as: _as, ...props },
  ref,
) {
  const inputId = id ?? props.name ?? label.toLowerCase().replace(/\\s+/g, '-');
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <FieldShell
      label={label}
      optional={optional}
      hint={hint}
      error={error}
      id={inputId}
      className={className}
    >
      <textarea
        ref={ref}
        id={inputId}
        className={cn(styles.control, styles.textarea)}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        {...props}
      />
    </FieldShell>
  );
});
