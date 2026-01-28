import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { GraduationCap, Mail, Lock, User, AlertCircle, Building2, ChevronDown } from 'lucide-react';
import { institutionsApi } from '../services/api';
import type { Institution } from '../types';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [institutionId, setInstitutionId] = useState('');
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loadingInstitutions, setLoadingInstitutions] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  // Fetch institutions on mount
  useEffect(() => {
    const fetchInstitutions = async () => {
      try {
        const data = await institutionsApi.getAll();
        setInstitutions(data);
        if (data.length > 0) {
          setInstitutionId(data[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch institutions:', err);
        setError('Failed to load institutions. Please refresh the page.');
      } finally {
        setLoadingInstitutions(false);
      }
    };
    fetchInstitutions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!institutionId) {
      setError('Please select your institution');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      const resetRequired = await register(email, password, fullName, institutionId);
      
      // Check if registration was successful but requires approval
      if (resetRequired === false && !error) {
        // Student registration - show success message about pending approval
        setSuccess('Registration successful! Your account is pending admin approval. You will receive an email once approved.');
        // Clear form
        setFullName('');
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        return;
      }
      
      // Don't navigate if password reset is required - modal will handle it
      if (!resetRequired) {
        navigate('/dashboard');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedInstitution = institutions.find(i => i.id === institutionId);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/30 mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Create Account</h1>
          <p className="text-slate-600 mt-2">Join Student Counsellor today</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-100 rounded-xl flex items-center gap-3 text-green-700">
              <p className="text-sm">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Institution Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Your Institution
              </label>
              <div className="relative">
                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <select
                  value={institutionId}
                  onChange={(e) => setInstitutionId(e.target.value)}
                  disabled={loadingInstitutions}
                  className="w-full pl-12 pr-10 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all appearance-none bg-white disabled:bg-slate-50 disabled:cursor-not-allowed"
                  required
                >
                  {loadingInstitutions ? (
                    <option value="">Loading institutions...</option>
                  ) : institutions.length === 0 ? (
                    <option value="">No institutions available</option>
                  ) : (
                    <>
                      <option value="">Select your institution</option>
                      {institutions.map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.name}
                        </option>
                      ))}
                    </>
                  )}
                </select>
                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
              </div>
              {selectedInstitution && (
                <p className="mt-1.5 text-xs text-slate-500">
                  {selectedInstitution.domain && `Domain: @${selectedInstitution.domain}`}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>

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
                  placeholder="At least 8 characters"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Confirm your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || loadingInstitutions || !institutionId}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-indigo-600 font-semibold hover:text-indigo-700"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
