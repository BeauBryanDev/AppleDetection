import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Label } from '../components/ui/Label';
import { Sprout, User, Mail, Phone, Lock, CheckCircle } from 'lucide-react';
import { registerRequest } from '../api/auth';

function RegisterPage() {
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Watch password for confirmation validation
  const password = watch('password');

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard');
  }, [isAuthenticated, navigate]);

  const onSubmit = handleSubmit(async (data) => {
    try {
      setLoading(true);
      setError(null);

      // Call the register endpoint
      await registerRequest({
        name: data.name,
        email: data.email,
        phone_number: data.phone_number || null,
        password: data.password
      });

      setSuccess(true);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);

    } catch (err) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || 'Error al registrar usuario');
    } finally {
      setLoading(false);
    }
  });

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cyber-black bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-cyber-black to-cyber-black p-4">
        <Card className="w-full max-w-md border-t-4 border-t-apple-green shadow-2xl">
          <div className="text-center py-8">
            <div className="flex justify-center mb-4">
              <div className="p-4 bg-apple-green/10 rounded-full border border-apple-green/30">
                <CheckCircle className="w-12 h-12 text-apple-green" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2"> Account created successfully </h2>
            <p className="text-zinc-400 mb-4">Your account has been created successfully</p>
            <p className="text-sm text-zinc-500 font-mono">Redirecting to login...</p>
          </div>
        </Card>
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Create a New  <span className="text-apple-green">Farm </span>
          </h1>
          <p className="text-zinc-500 mt-2 text-sm font-mono">CREATE FARMER ACCOUNT</p>
        </div>

        {/* Mostrar errores */}
        {error && (
          <div className="bg-apple-red/10 border border-apple-red/50 text-apple-red p-3 rounded mb-4 text-sm text-center font-bold animate-pulse">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <Label htmlFor="name">Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                className="pl-10"
                {...register("name", {
                  required: "name is required",
                  minLength: { value: 3, message: "Minimum 3 characters" }
                })}
                error={errors.name}
              />
            </div>
            {errors.name && (
              <p className="text-xs text-apple-red mt-1">{errors.name.message}</p>
            )}
          </div>

          {/* Email */}
          <div>
            <Label htmlFor="email">Email Address</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="email"
                type="email"
                placeholder="agricultor@agro.com"
                className="pl-10"
                {...register("email", {
                  required: "The email is required",
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: "Invalid email address"
                  }
                })}
                error={errors.email}
              />
            </div>
            {errors.email && (
              <p className="text-xs text-apple-red mt-1">{errors.email.message}</p>
            )}
          </div>

          {/* Phone (Optional) */}
          <div>
            <Label htmlFor="phone_number">Phone Number (Optional)</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="phone_number"
                type="tel"
                placeholder="+57 300 123 4567"
                className="pl-10"
                {...register("phone_number")}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                className="pl-10"
                {...register("password", {
                  required: "Password is required",
                  minLength: { value: 6, message: "Minimum 6 characters" }
                })}
                error={errors.password}
              />
            </div>
            {errors.password && (
              <p className="text-xs text-apple-red mt-1">{errors.password.message}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                className="pl-10"
                {...register("confirmPassword", {
                  required: "Confirm your password",
                  validate: value => value === password || "Passwords do not match"
                })}
                error={errors.confirmPassword}
              />
            </div>
            {errors.confirmPassword && (
              <p className="text-xs text-apple-red mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button type="submit" variant="primary" className="w-full" isLoading={loading}>
            <User className="w-4 h-4" /> Create Account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-500">
          Already have an account?{" "}
          <Link to="/login" className="text-apple-green hover:underline font-bold">
            Sign In
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

export default RegisterPage;
