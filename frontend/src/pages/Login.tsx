import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { GraduationCap, Mail, Lock, AlertCircle } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    if (searchParams.get('reason') === 'session_expired') {
      setSessionExpired(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSessionExpired(false);
    setIsLoading(true);

    try {
      const { resetRequired, isSuperAdmin } = await login(email, password);
      // Always navigate on success. If reset required, PasswordResetModal will show on dashboard.
      if (resetRequired) {
        navigate('/dashboard');
      } else {
        navigate(isSuperAdmin ? '/super-admin' : '/dashboard');
      }
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: string | unknown[] } } };
      const detail = ax.response?.data?.detail;
      const status = ax.response?.status;
      let message: string;
      if (status === 401) {
        message = typeof detail === 'string' ? detail : 'Incorrect email or password';
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        message = (detail[0] as { msg?: string })?.msg ?? 'Validation error';
      } else if (!ax.response) {
        message = 'Cannot reach server. Is the backend running?';
      } else {
        message = status === 500
          ? 'Server error during login. Check backend logs or try again.'
          : 'Login failed. Please try again.';
        if (status) message += ` (HTTP ${status})`;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/30 mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Welcome Back</h1>
          <p className="text-slate-600 mt-2">Sign in to your Student Counsellor account</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8">
          {sessionExpired && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-center gap-3 text-amber-800">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">Your session expired. Please sign in again.</p>
            </div>
          )}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 space-y-3 text-center">
            <p className="text-slate-600">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-indigo-600 font-semibold hover:text-indigo-700"
              >
                Create one
              </Link>
            </p>
            <p>
              <Link
                to="/forgot-password"
                className="text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                Forgot your password?
              </Link>
            </p>
            <p className="text-xs text-slate-400 mt-4">
              Super admin: <code className="bg-slate-100 px-1 rounded">super@adminsca.com</code> / <code className="bg-slate-100 px-1 rounded">SuperAdmin123!</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
