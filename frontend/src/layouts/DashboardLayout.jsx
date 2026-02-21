import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sidebar } from '../components/common/Sidebar';
import { Header } from '../components/common/Header';
import { Footer } from '../components/common/Footer';

export function DashboardLayout() {
  const { isAuthenticated, isGuest, loading } = useAuth();

  // 1. Si está cargando (verificando token), mostramos un spinner
  if (loading) {
    return (
      <div className="min-h-screen bg-cyber-black flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin"></div>
      </div>
    );
  }

  // 2. Si NO está autenticado Y NO es guest, lo mandamos al Login
  if (!isAuthenticated && !isGuest) {
    return <Navigate to="/login" replace />;
  }

  // 3. Si todo está bien, mostramos la App
  return (
    <div className="min-h-screen bg-cyber-black text-white font-sans flex">
      {/* Barra Lateral Fija */}
      <Sidebar />

      {/* Contenido Principal */}
      <main className="flex-1 lg:ml-64 flex flex-col min-h-screen pb-20 lg:pb-0">
        <Header />

        {/* Aquí se renderizan las páginas (Dashboard, Estimator, etc.) */}
        <div className="flex-1 p-4 sm:p-6 lg:p-8 xl:p-10 fade-in-animation">
          <Outlet />
        </div>
        <Footer />
      </main>
    </div>
  );
}
