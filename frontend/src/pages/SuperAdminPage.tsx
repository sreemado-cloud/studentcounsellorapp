import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { institutionsApi, adminApi } from '../services/api';
import type { User } from '../types';
import {
  Shield,
  ShieldOff,
  Users,
  Building2,
  Mail,
  AlertCircle,
  Check,
  X,
  Loader2,
  School,
  Plus,
  Lock,
  LockKeyhole,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';

export default function SuperAdminPage() {
  const { user } = useAuth();
  const [admins, setAdmins] = useState<User[]>([]);
  const [platformSummary, setPlatformSummary] = useState<{
    count: number;
    institutions: { id: string; name: string; is_active: boolean; tenant_isolation_level: string }[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [showAddInstitution, setShowAddInstitution] = useState(false);
  const [newInstName, setNewInstName] = useState('');
  const [newInstDomain, setNewInstDomain] = useState('');
  const [newInstIsolation, setNewInstIsolation] = useState<'high' | 'low'>('high');
  const [addingInst, setAddingInst] = useState(false);
  const [addInstError, setAddInstError] = useState('');

  useEffect(() => {
    fetchAdmins();
  }, []);

  useEffect(() => {
    if (user?.is_super_admin) {
      fetchPlatformSummary();
    }
  }, [user?.is_super_admin]);

  const fetchAdmins = async () => {
    try {
      setError('');
      // Super admin: include inactive, request higher limit to see all admins across the platform
      const data = await institutionsApi.getUsers('admin', true, 500);
      setAdmins(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admins');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPlatformSummary = async () => {
    if (!user?.is_super_admin) return;
    try {
      const data = await institutionsApi.getPlatformSummary();
      setPlatformSummary(data);
    } catch {
      setPlatformSummary({ count: 0, institutions: [] });
    }
  };

  const handleAddInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddInstError('');
    const name = newInstName.trim();
    if (!name) {
      setAddInstError('Institution name is required.');
      return;
    }
    setAddingInst(true);
    try {
      await institutionsApi.createInstitution({
        name,
        domain: newInstDomain.trim() || undefined,
        tenant_isolation_level: newInstIsolation,
      });
      setSuccess(`Institution "${name}" created successfully.`);
      setNewInstName('');
      setNewInstDomain('');
      setNewInstIsolation('high');
      setShowAddInstitution(false);
      await fetchPlatformSummary();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setAddInstError(ax.response?.data?.detail ?? 'Failed to create institution.');
    } finally {
      setAddingInst(false);
    }
  };

  const handleToggleStatus = async (admin: User) => {
    if (!user?.is_super_admin) return;
    if (admin.id === user?.id) {
      setError('You cannot disable your own account.');
      return;
    }
    setError('');
    setSuccess('');
    setUpdatingId(admin.id);
    try {
      await adminApi.updateUserStatus(admin.id, !admin.is_active);
      setSuccess(admin.is_active ? 'Admin disabled successfully.' : 'Admin enabled successfully.');
      await fetchAdmins();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update admin status');
    } finally {
      setUpdatingId(null);
    }
  };

  if (!user?.is_super_admin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <ShieldOff className="w-16 h-16 text-red-400" />
        <h2 className="text-xl font-semibold text-slate-800">Access denied</h2>
        <p className="text-slate-600 max-w-md text-center">
          This page is only available to super admins. Contact your super admin if you need access.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-12 h-12 animate-spin text-indigo-600" />
      </div>
    );
  }

  const superAdmins = admins.filter((a) => a.is_super_admin);
  const regularAdmins = admins.filter((a) => !a.is_super_admin);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Super Admin</h1>
        <p className="text-slate-600 mt-1">
          Manage admins. Only super admins can view this page and disable admin accounts.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="p-4 bg-green-50 border border-green-100 rounded-xl flex items-center gap-3 text-green-700">
          <Check className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{success}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
              <School className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{platformSummary?.count ?? '—'}</p>
              <p className="text-xs text-slate-500">Institutions (Tenants)</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{superAdmins.length}</p>
              <p className="text-xs text-slate-500">Super Admins</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{regularAdmins.length}</p>
              <p className="text-xs text-slate-500">Regular Admins</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{admins.length}</p>
              <p className="text-xs text-slate-500">Total Admins</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-indigo-600" />
              All Institutions (Tenants)
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {platformSummary
                ? `Platform-wide list of institutions. Total: ${platformSummary.count}.`
                : 'Loading…'}
            </p>
          </div>
            <div className="flex items-center gap-3">
              <Link
                to="/institutions"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-indigo-200 text-indigo-700 font-medium hover:bg-indigo-50 transition-colors"
              >
                Institutions →
              </Link>
              <button
                type="button"
                onClick={() => {
                  setShowAddInstitution(true);
                  setAddInstError('');
                  setNewInstName('');
                  setNewInstDomain('');
                  setNewInstIsolation('high');
                }}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Add institution
              </button>
            </div>
        </div>
        {!platformSummary ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-10 h-10 animate-spin text-indigo-600" />
          </div>
        ) : platformSummary.institutions.length === 0 ? (
            <div className="text-center py-12">
              <School className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No institutions on the platform</p>
              <button
                type="button"
                onClick={() => {
                  setShowAddInstitution(true);
                  setAddInstError('');
                  setNewInstName('');
                  setNewInstDomain('');
                  setNewInstIsolation('high');
                }}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Add institution
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Institution Name</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Tenant isolation</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {platformSummary.institutions.map((inst) => (
                    <tr key={inst.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          <span className="font-medium text-slate-800">{inst.name}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                            inst.tenant_isolation_level === 'high'
                              ? 'bg-indigo-100 text-indigo-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {inst.tenant_isolation_level === 'high' ? (
                            <Lock className="w-3 h-3" />
                          ) : (
                            <LockKeyhole className="w-3 h-3" />
                          )}
                          {inst.tenant_isolation_level === 'high' ? 'High' : 'Low'}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                            inst.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {inst.is_active ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                          {inst.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      {showAddInstitution && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => {
            setShowAddInstitution(false);
            setAddInstError('');
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-institution-title"
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 id="add-institution-title" className="text-lg font-semibold text-slate-800">Add institution</h3>
              <button
                type="button"
                onClick={() => {
                  setShowAddInstitution(false);
                  setAddInstError('');
                }}
                className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddInstitution} className="space-y-4">
              {addInstError && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {addInstError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Institution name *</label>
                <input
                  type="text"
                  value={newInstName}
                  onChange={(e) => setNewInstName(e.target.value)}
                  placeholder="e.g. State University"
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Domain (optional)</label>
                <input
                  type="text"
                  value={newInstDomain}
                  onChange={(e) => setNewInstDomain(e.target.value)}
                  placeholder="e.g. stateuniversity.edu"
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Tenant isolation level</label>
                <div className="flex gap-3">
                  <label
                    className={`flex-1 flex flex-col gap-1 p-3 border rounded-xl cursor-pointer transition-colors ${
                      newInstIsolation === 'high' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="isolation"
                        checked={newInstIsolation === 'high'}
                        onChange={() => setNewInstIsolation('high')}
                        className="text-indigo-600"
                      />
                      <Lock className="w-4 h-4 text-indigo-600" />
                      <span className="font-medium text-slate-800">High</span>
                    </div>
                    <span className="text-xs text-slate-500 pl-6">Dedicated DB/instances</span>
                  </label>
                  <label
                    className={`flex-1 flex flex-col gap-1 p-3 border rounded-xl cursor-pointer transition-colors ${
                      newInstIsolation === 'low' ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="isolation"
                        checked={newInstIsolation === 'low'}
                        onChange={() => setNewInstIsolation('low')}
                        className="text-indigo-600"
                      />
                      <LockKeyhole className="w-4 h-4 text-slate-600" />
                      <span className="font-medium text-slate-800">Low</span>
                    </div>
                    <span className="text-xs text-slate-500 pl-6">Shared resources</span>
                  </label>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddInstitution(false);
                    setAddInstError('');
                  }}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingInst}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  {addingInst ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                      Creating…
                    </>
                  ) : (
                    'Create'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-800">Admins</h2>
          <p className="text-sm text-slate-500 mt-1">
            Disable or enable admin accounts. You cannot disable your own account or other super admins.
          </p>
        </div>
        {admins.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No admins on the platform</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Admin</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600 hidden md:table-cell">Institution</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600 hidden lg:table-cell">Joined</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {admins.map((a) => {
                  const isCurrentUser = a.id === user?.id;
                  return (
                    <tr key={a.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                            {a.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-slate-800">{a.full_name}</p>
                              {a.is_super_admin && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                                  <Shield className="w-3 h-3" />
                                  Super Admin
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-slate-500 flex items-center gap-1.5">
                              <Mail className="w-3.5 h-3.5" />
                              {a.email}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6 hidden md:table-cell">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          <span className="text-sm text-slate-700">{a.institution_name ?? '—'}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6 hidden lg:table-cell">
                        <p className="text-sm text-slate-600">
                          {format(parseISO(a.created_at), 'MMM d, yyyy')}
                        </p>
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                            a.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {a.is_active ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                          {a.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        {isCurrentUser ? (
                          <span className="text-sm text-slate-400">(You)</span>
                        ) : a.is_super_admin ? (
                          <span className="text-sm text-slate-400">—</span>
                        ) : (
                          <button
                            onClick={() => handleToggleStatus(a)}
                            disabled={!!updatingId}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                              a.is_active
                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                : 'bg-green-100 text-green-700 hover:bg-green-200'
                            }`}
                          >
                            {updatingId === a.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : a.is_active ? (
                              <>
                                <ShieldOff className="w-4 h-4" />
                                Disable
                              </>
                            ) : (
                              <>
                                <Check className="w-4 h-4" />
                                Enable
                              </>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
