import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { GraduationCap, Mail, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setIsLoading(true);

    try {
      console.log('Sending forgot password request for:', email);
      
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout - please try again')), 30000);
      });
      
      const response = await Promise.race([
        authApi.forgotPassword(email),
        timeoutPromise
      ]) as { message?: string };
      
      console.log('Forgot password response:', response);
      
      // Check if we got a valid response
      if (response && (response.message || typeof response === 'object')) {
        setSuccess(true);
        setIsLoading(false);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: unknown) {
      console.error('Forgot password error:', err);
      const error = err as { 
        response?: { 
          data?: { detail?: string };
          status?: number;
        }; 
        message?: string;
        code?: string;
      };
      
      let errorMessage = 'Failed to send reset email. Please try again.';
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'Request timed out. Please check your connection and try again.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait a moment and try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
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
          <h1 className="text-3xl font-bold text-slate-800">Forgot Password?</h1>
          <p className="text-slate-600 mt-2">Enter your email to receive reset instructions</p>
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
              <h2 className="text-xl font-semibold text-slate-800 mb-2">Check Your Email</h2>
              <p className="text-slate-600 mb-6">
                If an account with that email exists, we've sent password reset instructions to{' '}
                <span className="font-semibold text-slate-800">{email}</span>
              </p>
              <p className="text-sm text-slate-500 mb-6">
                Please check your inbox and follow the instructions to reset your password.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-indigo-600 font-semibold hover:text-indigo-700"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          ) : (
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
                    autoFocus
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sending...' : 'Send Reset Instructions'}
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
