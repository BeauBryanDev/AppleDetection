import { forwardRef } from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Input = forwardRef(({ className, error, ...props }, ref) => {
  return (
    <div className="w-full">
      <input
        ref={ref}
        className={twMerge(
          clsx(
            "w-full bg-black/50 border rounded-lg px-4 py-3 text-white placeholder-zinc-500 outline-none transition-all duration-300",
            // Estado Normal vs Error
            error 
              ? "border-apple-red focus:shadow-neon-red" 
              : "border-zinc-700 focus:border-apple-green focus:shadow-neon-green",
            className
          )
        )}
        {...props}
      />
      {error && (
        <span className="text-apple-red text-xs mt-1 block font-mono tracking-wide">
          ⚠️ {error.message}
        </span>
      )}
    </div>
  );
});

Input.displayName = "Input";