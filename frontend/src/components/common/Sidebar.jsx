import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  History,
  Trees,
  BarChart3,
  Shield,
  Sprout,
  User
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../../context/AuthContext';

export function Sidebar() {
  const { user, isGuest } = useAuth();

  const allNavItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: Zap, label: 'Estimador AI', path: '/estimator' },
    { icon: Trees, label: 'Mis Huertos', path: '/farming' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: History, label: 'Historial', path: '/history' },
    { icon: User, label: 'Mi Perfil', path: '/profile' },
    // Admin-only item
    ...(user?.role === 'admin' ? [{ icon: Shield, label: 'Usuarios', path: '/users' }] : []),
  ];

  // Filter items for guest mode
  const navItems = isGuest
    ? allNavItems.filter(item => item.label === 'Estimador AI')
    : allNavItems;

  return (
    <aside className="fixed inset-x-0 bottom-0 z-50 h-16 bg-cyber-dark border-t border-zinc-800 lg:inset-x-auto lg:left-0 lg:top-0 lg:bottom-auto lg:h-screen lg:w-64 lg:border-r lg:border-t-0 flex flex-col">
      {/* Logo Area */}
      <div className="hidden lg:flex h-16 items-center px-6 border-b border-zinc-800">
        <Sprout className="w-6 h-6 text-apple-green mr-2" />
        <span className="text-lg font-bold text-white tracking-wider">
          Yield<span className="text-apple-green">Estimator</span>
        </span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-2 py-2 lg:py-6 lg:px-3 flex items-center justify-between lg:block lg:space-y-1 overflow-x-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx(
              "flex items-center justify-center lg:justify-start gap-2 lg:gap-3 px-2 sm:px-3 py-2 lg:py-3 rounded-lg transition-all duration-200 group min-w-[56px] sm:min-w-[64px] lg:min-w-0",
              isActive
                ? "bg-apple-green/10 text-apple-green border border-apple-green/20 shadow-neon-green"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800"
            )}
          >
            <item.icon className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="hidden lg:inline font-medium text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer del Sidebar */}
      <div className="hidden lg:block p-4 border-t border-zinc-800">
        <div className="bg-zinc-900/50 rounded p-3 text-xs text-zinc-500 font-mono text-center">
          v1.0.0 Stable
        </div>
      </div>
    </aside>
  );
}
