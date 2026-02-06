import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Label } from '../components/ui/Label';
import { Sprout, Lock } from 'lucide-react'; // Iconos temáticos

function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const { signin, isAuthenticated, errors: loginErrors, loading } = useAuth();
  const navigate = useNavigate();

  // Si ya está logueado, redirigir al Dashboard
  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard');
  }, [isAuthenticated, navigate]);

  const onSubmit = handleSubmit(async (data) => {
    await signin(data.email, data.password);
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-cyber-black bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-cyber-black to-cyber-black p-4">
      
      <Card className="w-full max-w-md border-t-4 border-t-apple-green shadow-2xl relative overflow-hidden">
        
        {/* Efecto decorativo de fondo */}
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-apple-green/10 rounded-full blur-2xl"></div>

        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-zinc-900 rounded-full border border-zinc-800 shadow-neon-green">
              <Sprout className="w-8 h-8 text-apple-green" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Yield<span className="text-apple-green">Estimator</span></h1>
          <p className="text-zinc-500 mt-2 text-sm font-mono">ACCESO AL SISTEMA AGRÍCOLA v1.0</p>
        </div>

        {/* Mostrar errores del backend (ej: credenciales inválidas) */}
        {loginErrors.map((err, i) => (
          <div key={i} className="bg-apple-red/10 border border-apple-red/50 text-apple-red p-3 rounded mb-4 text-sm text-center font-bold animate-pulse">
            ⚠️ {err}
          </div>
        ))}

        <form onSubmit={onSubmit} className="space-y-6">
          <div>
            <Label htmlFor="email">Correo Electrónico</Label>
            <Input
              type="email"
              placeholder="agricultor@agro.com"
              {...register("email", { required: "El correo es requerido" })}
              error={errors.email}
            />
          </div>

          <div>
            <Label htmlFor="password">Contraseña</Label>
            <Input
              type="password"
              placeholder="••••••••"
              {...register("password", { required: "La contraseña es requerida" })}
              error={errors.password}
            />
          </div>

          <Button type="submit" variant="primary" className="w-full" isLoading={loading}>
            <Lock className="w-4 h-4" /> INICIAR SESIÓN
          </Button>
        </form>

        <p className="mt-8 text-center text-sm text-zinc-500">
          ¿No tienes cuenta?{" "}
          <Link to="/register" className="text-apple-green hover:underline font-bold">
            Registrar Finca
          </Link>
        </p>
      </Card>
      
      {/* Footer minimalista */}
      <div className="absolute bottom-4 text-zinc-700 text-xs font-mono">
        SYSTEM STATUS: <span className="text-apple-green">ONLINE</span>
      </div>
    </div>
  );
}

export default LoginPage;