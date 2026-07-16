import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
  children: ReactNode;
};

const variants = {
  primary: 'bg-cedar text-white hover:bg-teal-800 focus-visible:outline-cedar',
  secondary: 'border border-cedar text-cedar hover:bg-teal-50 dark:hover:bg-teal-950',
  ghost: 'text-ink hover:bg-slate-100 dark:text-white dark:hover:bg-slate-800',
};

export function Button({ variant = 'primary', className = '', children, ...props }: ButtonProps) {
  return (
    <button
      className={`min-h-11 rounded-md px-5 py-2.5 font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 motion-reduce:transition-none disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
