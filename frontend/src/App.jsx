import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/Login';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Ruta temporal para ver el Login */}
          <Route path="/" element={<LoginPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<div className='text-white text-center mt-20'>Página de Registro (Pendiente)</div>} />
          <Route path="/dashboard" element={<div className='text-apple-green text-center mt-20 text-3xl font-bold'>🌱 BIENVENIDO AL DASHBOARD 🌱</div>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;