import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Apple, Lock, Mail, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const navigate = useNavigate();
  const { signin, enterAsGuest, errors, isAuthenticated } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  // Redirect to dashboard when user is authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await signin(formData.email, formData.password);
      // Navigation happens via useEffect when isAuthenticated changes
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestAccess = () => {
    enterAsGuest();
    navigate('/estimator');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyber-black via-zinc-950 to-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-apple-green to-green-600 rounded-2xl mb-4 shadow-2xl shadow-apple-green/20">
            <Apple className="w-10 h-10 text-black" />
          </div>
          <h1 className="text-4xl font-black text-white mb-2 tracking-tight">
            Apple Yield Estimator
          </h1>
          <p className="text-zinc-400 font-mono text-sm">
            Sign in to access your orchards
          </p>
        </div>

        {/* Login Card */}
        <Card className="p-8 bg-black/40 border-zinc-800 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">
                Email Address
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="pl-11 bg-zinc-900/50 border-zinc-700 text-white placeholder:text-zinc-600 focus:border-apple-green"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">
                Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="pl-11 bg-zinc-900/50 border-zinc-700 text-white placeholder:text-zinc-600 focus:border-apple-green"
                />
              </div>
            </div>

            {/* Error Messages */}
            {errors && errors.length > 0 && (
              <div className="p-4 bg-apple-red/10 border border-apple-red/30 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-apple-red flex-shrink-0 mt-0.5" />
                <div className="text-sm text-apple-red">
                  {errors.map((error, i) => (
                    <div key={i}>{error}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-apple-green hover:bg-apple-green/90 text-black font-bold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-apple-green/20"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
                  Signing in...
                </div>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-black text-zinc-500 font-mono">OR</span>
            </div>
          </div>

          {/* Guest Access Button */}
          <Button
            type="button"
            onClick={handleGuestAccess}
            variant="outline"
            className="w-full border-zinc-700 hover:border-apple-green text-zinc-300 hover:text-apple-green py-3 rounded-lg transition-all"
          >
            Continue as Guest
          </Button>

          {/* Register Link */}
          <div className="mt-6 text-center text-sm text-zinc-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-apple-green hover:underline font-bold">
              Create one
            </Link>
          </div>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-zinc-600 font-mono">
          &copy; 2025 Apple Yield Estimator. Powered by YOLOv8.
        </div>
      </div>
    </div>
  );
}
