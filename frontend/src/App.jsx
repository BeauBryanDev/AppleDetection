import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import { DashboardLayout } from './layouts/DashboardLayout';
import DashboardPage from './pages/Dashboard';
import EstimatorPage from './pages/Estimator';
import FarmingPage from './pages/Farming';
import AnalyticsPage from './pages/Analytics';
import HistoryPage from './pages/History';
import UsersPage from './pages/Users';
import ProfilePage from './pages/Profile';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rutas Públicas */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Redirección raíz */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Rutas Protegidas (Layout aplica a todas estas) */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/estimator" element={<EstimatorPage />} />
            <Route path="/farming" element={<FarmingPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;