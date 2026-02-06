import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/Login';
import { DashboardLayout } from './layouts/DashboardLayout';
import DashboardPage from './pages/Dashboard';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rutas Públicas */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Redirección raíz */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Rutas Protegidas (Layout aplica a todas estas) */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/estimator" element={<div className="text-white">Página Estimador (Pendiente)</div>} />
            <Route path="/history" element={<div className="text-white">Página Historial (Pendiente)</div>} />
            <Route path="/settings" element={<div className="text-white">Página Configuración (Pendiente)</div>} />
          </Route>
          
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;