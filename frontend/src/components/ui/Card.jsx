import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Card({ children, className }) {
  return (
    <div
      className={twMerge(
        clsx(
          "bg-cyber-gray/80 backdrop-blur-md border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-xl",
          "hover:border-zinc-700 transition-all duration-300",
          className
        )
      )}
    >
      {children}
    </div>
  );
}
