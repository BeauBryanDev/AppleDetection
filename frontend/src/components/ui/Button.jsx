import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Button({ children, className, variant = "primary", isLoading, ...props }) {
  const variants = {
    primary: "bg-apple-green text-black hover:bg-apple-green-dim shadow-neon-green hover:shadow-none font-bold",
    danger: "bg-apple-red text-white hover:bg-apple-red-dim shadow-neon-red hover:shadow-none font-bold",
    outline: "bg-transparent border border-apple-green text-apple-green hover:bg-apple-green/10",
    ghost: "bg-transparent text-zinc-400 hover:text-white hover:bg-white/5",
  };

  return (
    <button
      disabled={isLoading}
      className={twMerge(
        clsx(
          "px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base",
          variants[variant],
          className
        )
      )}
      {...props}
    >
      {isLoading ? (
        // Spinner de carga minimalista
        <div className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
      ) : (
        children
      )}
    </button>
  );
}
