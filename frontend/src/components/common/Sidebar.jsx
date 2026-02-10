import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  History,
  Trees,
  BarChart3,
  Shield,
  Sprout
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../../context/AuthContext';

export function Sidebar() {
  const { user } = useAuth();

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: Zap, label: 'Estimador AI', path: '/estimator' },
    { icon: Trees, label: 'Mis Huertos', path: '/farming' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: History, label: 'Historial', path: '/history' },
    // Admin-only item
    ...(user?.role === 'ADMIN' ? [{ icon: Shield, label: 'Usuarios', path: '/users' }] : []),
  ];

  return (
    <aside className="w-64 bg-cyber-dark border-r border-zinc-800 flex flex-col h-screen fixed left-0 top-0 z-50">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-zinc-800">
        <Sprout className="w-6 h-6 text-apple-green mr-2" />
        <span className="text-lg font-bold text-white tracking-wider">
          Yield<span className="text-apple-green">Estimator</span>
        </span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-6 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx(
              "flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group",
              isActive 
                ? "bg-apple-green/10 text-apple-green border border-apple-green/20 shadow-neon-green" 
                : "text-zinc-400 hover:text-white hover:bg-zinc-800"
            )}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer del Sidebar */}
      <div className="p-4 border-t border-zinc-800">
        <div className="bg-zinc-900/50 rounded p-3 text-xs text-zinc-500 font-mono text-center">
          v1.0.0 Stable
        </div>
      </div>
    </aside>
  );
}