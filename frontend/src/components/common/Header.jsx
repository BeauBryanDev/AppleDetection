import { LogOut, User, Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/Button';
import punkApple from '../../assets/punk_apple.svg';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-cyber-dark/80 backdrop-blur-md border-b border-zinc-800 flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Breadcrumbs o Título (Por ahora vacío o dinámico) */}
      <div className="text-zinc-400 text-sm font-mono">
        SYSTEM: <span className="text-apple-green">ONLINE</span>
      </div>

      {/* Area de Usuario */}
      <div className="flex items-center gap-4">
        {/* Notificaciones (Decorativo por ahora) */}
        <button className="p-2 text-zinc-400 hover:text-white transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-apple-red rounded-full animate-pulse"></span>
        </button>

        <div className="h-6 w-px bg-zinc-700 mx-2"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-bold text-white leading-none">{user?.name || 'Invitado'}</p>
            <p className="text-xs text-zinc-500 font-mono mt-1 uppercase">{user?.role || 'GUEST'}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-zinc-800 rounded-full flex items-center justify-center border border-zinc-700 text-apple-green">
              <User className="w-5 h-5" />
            </div>
            <img 
              src={punkApple} 
              alt="Punk Apple Logo" 
              className="w-10 h-10 filter drop-shadow-lg hover:drop-shadow-[0_0_8px_#22c55e] transition-all duration-300"
              title="Apple Yield Estimator"
            />
          </div>
        </div>

        <Button variant="ghost" onClick={logout} className="ml-2" title="Cerrar Sesión">
          <LogOut className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}