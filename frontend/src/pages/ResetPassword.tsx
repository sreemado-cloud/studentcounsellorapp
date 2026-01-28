import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { GraduationCap, Lock, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Invalid reset token');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.resetPasswordWithToken(token, password);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to reset password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-800 mb-2">Invalid Reset Link</h2>
            <p className="text-slate-600 mb-6">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Link
              to="/forgot-password"
              className="inline-flex items-center gap-2 text-indigo-600 font-semibold hover:text-indigo-700"
            >
              Request New Reset Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/30 mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Reset Password</h1>
          <p className="text-slate-600 mt-2">Enter your new password</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {success ? (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold text-slate-800 mb-2">Password Reset Successful!</h2>
              <p className="text-slate-600 mb-6">
                Your password has been reset successfully. You can now login with your new password.
              </p>
              <p className="text-sm text-slate-500">
                Redirecting to login page...
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    placeholder="Enter new password (min. 8 characters)"
                    required
                    minLength={8}
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Confirm New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    placeholder="Confirm new password"
                    required
                    minLength={8}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Resetting Password...' : 'Reset Password'}
              </button>
            </form>
          )}

          {!success && (
            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-slate-600 hover:text-indigo-600 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
