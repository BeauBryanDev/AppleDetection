import { Heart, Apple } from 'lucide-react';

export function Footer() {
  return (
    <footer className="w-full border-t border-zinc-800 bg-cyber-dark/80 backdrop-blur-sm">
      <div className="px-4 sm:px-6 lg:px-8 xl:px-10 py-3 flex items-center justify-center gap-2 text-xs sm:text-sm font-mono tracking-wide">
        <span className="text-zinc-500">Built</span>
        <Heart className="w-4 h-4 text-apple-red animate-pulse" />
        <span className="text-zinc-500">with</span>
        <span className="text-apple-green font-bold">Love for Apples</span>
        <Apple className="w-4 h-4 text-apple-green" />
      </div>
    </footer>
  );
}
