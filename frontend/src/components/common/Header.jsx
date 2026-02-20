import { useState, useEffect } from 'react';
import { LogOut, User, Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/Button';
import punkApple from '../../assets/punk_apple.svg';

export function Header() {
  const { user, logout } = useAuth();
  const [avatarUrl, setAvatarUrl] = useState(null);

  useEffect(() => {
    if (user?.id && user?.avatar_url) {
      loadAvatarUrl(user.id);
    }
  }, [user?.id, user?.avatar_url]);

  const loadAvatarUrl = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/v1/users/${userId}/profile-picture-url`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAvatarUrl(data.url);
      }
    } catch (err) {
      console.error('Error loading avatar:', err);
    }
  };
  useEffect(() => {
  if (user?.id) {
    loadAvatarUrl(user.id);
  }
}, [user?.id]);

  return (
    <header className="h-16 bg-cyber-dark/80 backdrop-blur-md border-b border-zinc-800 flex items-center justify-between px-3 sm:px-4 lg:px-6 sticky top-0 z-40">
      <div className="hidden sm:block text-zinc-400 text-sm font-mono">
        SYSTEM: <span className="text-apple-green">ONLINE</span>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 ml-auto">
        <button className="p-2 text-zinc-400 hover:text-white transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-apple-red rounded-full animate-pulse"></span>
        </button>

        <div className="hidden sm:block h-6 w-px bg-zinc-700 mx-1 lg:mx-2"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-bold text-white leading-none">{user?.name || 'Invitado'}</p>
            <p className="text-xs text-zinc-500 font-mono mt-1 uppercase">{user?.role || 'GUEST'}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-zinc-700 overflow-hidden bg-zinc-800 flex items-center justify-center text-apple-green">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Foto de perfil"
                  className="w-full h-full object-cover"
                  onError={() => setAvatarUrl(null)}
                />
              ) : (
                <User className="w-5 h-5" />
              )}
            </div>
            <img
              src={punkApple}
              alt="Punk Apple Logo"
              className="hidden sm:block w-9 h-9 lg:w-10 lg:h-10 filter drop-shadow-lg hover:drop-shadow-[0_0_8px_#22c55e] transition-all duration-300"
              title="Apple Yield Estimator"
            />
          </div>
        </div>

        <Button variant="ghost" onClick={logout} className="ml-1 sm:ml-2 px-2 sm:px-4" title="Cerrar Sesión">
          <LogOut className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}
