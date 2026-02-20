import { createContext, useState, useContext, useEffect } from 'react';
import { loginRequest, verifyTokenRequest, checkEmailExists } from '../api/auth';

const AuthContext = createContext();

// Hook personalizado para usar el contexto fácil
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isGuest, setIsGuest] = useState(false);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState([]);

  // Función de Login
  const signin = async (email, password) => {
    try {
      // First check if email exists
      const emailCheckRes = await checkEmailExists(email);
      
      if (!emailCheckRes.data.exists) {
        setErrors(["Email is not registered in database"]);
        return;
      }

      // If email exists, attempt login
      const res = await loginRequest(email, password);
      // Guardamos el token
      localStorage.setItem('token', res.data.access_token);
      setIsAuthenticated(true);
      setIsGuest(false);

      // Obtenemos los datos del usuario inmediatamente
      const userRes = await verifyTokenRequest();
      setUser(userRes.data);
      setErrors([]);
    } catch (error) {
      console.error(error);
      setErrors([error.response?.data?.detail || "Error during login"]);
    }
  };

  const enterAsGuest = () => {
    setIsGuest(true);
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('token');
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
    setIsGuest(false);
  };

  // Efecto: Verificar si ya existe un token al recargar la página
  useEffect(() => {
    async function checkLogin() {
      const token = localStorage.getItem('token');
      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      try {
        const res = await verifyTokenRequest();
        if (!res.data) {
          setIsAuthenticated(false);
          setLoading(false);
          return;
        }
        setIsAuthenticated(true);
        setIsGuest(false);
        setUser(res.data);
        setLoading(false);
      } catch (error) {
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
      }
    }
    checkLogin();
  }, []);

  return (
    <AuthContext.Provider value={{ signin, enterAsGuest, logout, user, isAuthenticated, isGuest, errors, loading, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};