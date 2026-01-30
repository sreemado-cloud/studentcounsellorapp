import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { institutionsApi, adminApi } from '../services/api';
import type { User, UserRole, Institution } from '../types';
import {
  Users,
  UserPlus,
  Search,
  Shield,
  GraduationCap,
  Briefcase,
  Calendar,
  X,
  Check,
  AlertCircle,
  Building2,
  UserCheck,
  ArrowRightLeft,
  ChevronDown,
  Key,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';

interface NewUserForm {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  assigned_counsellor_id?: string;
  phone?: string;
}

const roleConfig: Record<UserRole, { label: string; icon: typeof Users; color: string; bgColor: string }> = {
  admin: { label: 'Admin', icon: Shield, color: 'text-purple-700', bgColor: 'bg-purple-100' },
  counsellor: { label: 'Counsellor', icon: Briefcase, color: 'text-emerald-700', bgColor: 'bg-emerald-100' },
  student: { label: 'Student', icon: GraduationCap, color: 'text-blue-700', bgColor: 'bg-blue-100' },
};

export default function AdminPanel() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showReassignModal, setShowReassignModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<User | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedCounsellorId, setSelectedCounsellorId] = useState<string>('');
  const [selectedInstitutionId, setSelectedInstitutionId] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const [isReassigning, setIsReassigning] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [userForResetPassword, setUserForResetPassword] = useState<User | null>(null);
  const [resetPasswordNew, setResetPasswordNew] = useState('');
  const [resetPasswordConfirm, setResetPasswordConfirm] = useState('');
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newUser, setNewUser] = useState<NewUserForm>({
    email: '',
    password: '',
    full_name: '',
    role: 'counsellor',
    phone: '',
  });

  useEffect(() => {
    fetchUsers();
    fetchInstitutions();
  }, []);

  const fetchUsers = async () => {
    try {
      // Super admin: include inactive users and request more rows so no one is missed
      const includeInactive = user?.is_super_admin === true;
      const limit = includeInactive ? 300 : undefined;
      const data = await institutionsApi.getUsers(undefined, includeInactive, limit);
      setUsers(data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchInstitutions = async () => {
    try {
      const data = await institutionsApi.getAll();
      setInstitutions(data);
    } catch (error) {
      console.error('Failed to fetch institutions:', error);
    }
  };

  const counsellors = users.filter((u) => u.role === 'counsellor' && u.is_active);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newUser.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          ...newUser,
          // institution_id is automatically set by backend to admin's institution
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create user');
      }

      await response.json();
      setSuccess(`${roleConfig[newUser.role].label} "${newUser.full_name}" created successfully!`);
      setNewUser({
        email: '',
        password: '',
        full_name: '',
        role: 'counsellor',
        phone: '',
      });
      setShowAddModal(false);
      await fetchUsers();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAssignStudent = async () => {
    if (!selectedStudent) return;

    setError('');
    setSuccess('');
    setIsAssigning(true);

    try {
      const response = await fetch(`/api/admin/users/${selectedStudent.id}/assign-counsellor`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          counsellor_id: selectedCounsellorId || null,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to assign student');
      }

      const result = await response.json();
      await fetchUsers();

      setSuccess(
        result.assigned_counsellor_id
          ? `Student assigned to ${result.assigned_counsellor_name} successfully!`
          : 'Student unassigned successfully!'
      );

      setTimeout(() => {
        setShowAssignModal(false);
        setSelectedStudent(null);
        setSelectedCounsellorId('');
        setSuccess('');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign student');
    } finally {
      setIsAssigning(false);
    }
  };

  const openAssignModal = (student: User) => {
    setSelectedStudent(student);
    setSelectedCounsellorId(student.assigned_counsellor_id || '');
    setShowAssignModal(true);
    setError('');
    setSuccess('');
  };

  const openReassignModal = (userToReassign: User) => {
    setSelectedUser(userToReassign);
    setSelectedInstitutionId(userToReassign.institution_id);
    setShowReassignModal(true);
    setError('');
    setSuccess('');
  };

  const handleReassignInstitution = async () => {
    if (!selectedUser || !selectedInstitutionId) return;

    setError('');
    setSuccess('');
    setIsReassigning(true);

    try {
      const response = await fetch(`/api/admin/users/${selectedUser.id}/reassign-institution`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          new_institution_id: selectedInstitutionId,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to reassign user');
      }

      const result = await response.json();

      setSuccess(`User reassigned to ${result.new_institution_name} successfully!`);
      await fetchUsers();

      setTimeout(() => {
        setShowReassignModal(false);
        setSelectedUser(null);
        setSelectedInstitutionId('');
        setSuccess('');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reassign user');
    } finally {
      setIsReassigning(false);
    }
  };

  const openResetPasswordModal = (u: User) => {
    setUserForResetPassword(u);
    setResetPasswordNew('');
    setResetPasswordConfirm('');
    setShowResetPasswordModal(true);
    setError('');
    setSuccess('');
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userForResetPassword) return;
    if (resetPasswordNew.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (resetPasswordNew !== resetPasswordConfirm) {
      setError('Passwords do not match');
      return;
    }
    setError('');
    setSuccess('');
    setIsResettingPassword(true);
    try {
      await adminApi.setUserPassword(userForResetPassword.id, resetPasswordNew);
      setSuccess(`Password set for ${userForResetPassword.full_name}. They can now login with the new password.`);
      setTimeout(() => {
        setShowResetPasswordModal(false);
        setUserForResetPassword(null);
        setResetPasswordNew('');
        setResetPasswordConfirm('');
        setSuccess('');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set password');
    } finally {
      setIsResettingPassword(false);
    }
  };

  // Filter users
  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  // Group users by role for stats
  const userStats = {
    total: users.length,
    admins: users.filter((u) => u.role === 'admin').length,
    superAdmins: users.filter((u) => u.role === 'admin' && u.is_super_admin).length,
    regularAdmins: users.filter((u) => u.role === 'admin' && !u.is_super_admin).length,
    counsellors: users.filter((u) => u.role === 'counsellor').length,
    students: users.filter((u) => u.role === 'student').length,
    pendingStudents: users.filter((u) => u.role === 'student' && u.approval_status === 'pending').length,
  };

  const handleApproveStudent = async (userId: string) => {
    setError('');
    setSuccess('');
    try {
      await adminApi.approveStudent(userId);
      setSuccess('Student approved successfully!');
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve student');
    }
  };

  const handleRejectStudent = async (userId: string, reason?: string) => {
    setError('');
    setSuccess('');
    try {
      await adminApi.rejectStudent(userId, reason);
      setSuccess('Student registration rejected.');
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject student');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Admin Panel</h1>
          <div className="flex items-center gap-2 mt-1 text-slate-600">
            <Building2 className="w-4 h-4" />
            <span>{user?.institution_name || 'Your Institution'}</span>
          </div>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium"
        >
          <UserPlus className="w-5 h-5" />
          Add User
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{userStats.total}</p>
              <p className="text-xs text-slate-500">Total Users</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{userStats.admins}</p>
              <p className="text-xs text-slate-500">
                Admins
                {userStats.superAdmins > 0 && (
                  <span className="ml-1 text-amber-600">({userStats.superAdmins} super)</span>
                )}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{userStats.counsellors}</p>
              <p className="text-xs text-slate-500">Counsellors</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{userStats.students}</p>
              <p className="text-xs text-slate-500">Students</p>
            </div>
          </div>
        </div>
        {userStats.pendingStudents > 0 && (
          <div className="bg-white rounded-xl p-4 shadow-sm border border-amber-200 bg-amber-50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-amber-800">{userStats.pendingStudents}</p>
                <p className="text-xs text-amber-600">Pending Approval</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or email..."
              className="w-full pl-12 pr-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
          </div>
          <div className="flex gap-2">
            {(['all', 'admin', 'counsellor', 'student'] as const).map((role) => (
              <button
                key={role}
                onClick={() => setRoleFilter(role)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  roleFilter === role
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {role === 'all' ? 'All' : roleConfig[role].label + 's'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        {filteredUsers.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">
              {searchQuery || roleFilter !== 'all'
                ? 'No users match your filters'
                : 'No users found'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">User</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Role</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600 hidden lg:table-cell">Institution</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600 hidden lg:table-cell">Assigned Counsellor</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600 hidden lg:table-cell">Joined</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map((u) => {
                  const config = roleConfig[u.role];
                  const RoleIcon = config.icon;
                  return (
                    <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                            {u.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-slate-800">{u.full_name}</p>
                            <p className="text-sm text-slate-500">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex flex-col gap-1">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}>
                            <RoleIcon className="w-3.5 h-3.5" />
                            {config.label}
                          </span>
                          {u.role === 'admin' && u.is_super_admin && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                              <Shield className="w-3 h-3" />
                              Super Admin
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-6 hidden lg:table-cell">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          <span className="text-sm text-slate-700">{u.institution_name ?? '—'}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6 hidden lg:table-cell">
                        {u.role === 'student' ? (
                          u.assigned_counsellor_name ? (
                            <div className="flex items-center gap-2">
                              <Briefcase className="w-3.5 h-3.5 text-emerald-500" />
                              <span className="text-sm text-slate-700">{u.assigned_counsellor_name}</span>
                            </div>
                          ) : (
                            <span className="text-sm text-slate-400">—</span>
                          )
                        ) : (
                          <span className="text-sm text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-4 px-6 hidden lg:table-cell">
                        <p className="text-sm text-slate-600 flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          {format(parseISO(u.created_at), 'MMM d, yyyy')}
                        </p>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                          u.approval_status === 'pending'
                            ? 'bg-amber-100 text-amber-700'
                            : u.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {u.approval_status === 'pending' ? (
                            <>
                              <AlertCircle className="w-3 h-3" />
                              Pending
                            </>
                          ) : u.is_active ? (
                            <>
                              <Check className="w-3 h-3" />
                              Active
                            </>
                          ) : (
                            <>
                              <X className="w-3 h-3" />
                              Inactive
                            </>
                          )}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex flex-col gap-2">
                          {u.role === 'student' && u.approval_status === 'pending' && (
                            <>
                              <button
                                onClick={() => handleApproveStudent(u.id)}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors font-medium"
                              >
                                <Check className="w-4 h-4" />
                                Approve
                              </button>
                              <button
                                onClick={() => {
                                  const reason = prompt('Enter rejection reason (optional):');
                                  if (reason !== null) {
                                    handleRejectStudent(u.id, reason || undefined);
                                  }
                                }}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium"
                              >
                                <X className="w-4 h-4" />
                                Reject
                              </button>
                            </>
                          )}
                          {u.role === 'student' && u.approval_status !== 'pending' && (
                            <button
                              onClick={() => openAssignModal(u)}
                              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors font-medium"
                            >
                              <UserCheck className="w-4 h-4" />
                              {u.assigned_counsellor_id ? 'Reassign' : 'Assign'}
                            </button>
                          )}
                          {user?.is_super_admin && (u.role === 'admin' || u.role === 'counsellor' || (u.role === 'student' && u.approval_status !== 'pending')) && (
                            <button
                              onClick={() => openReassignModal(u)}
                              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors font-medium"
                            >
                              <ArrowRightLeft className="w-4 h-4" />
                              Reassign Inst.
                            </button>
                          )}
                          <button
                            onClick={() => openResetPasswordModal(u)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
                          >
                            <Key className="w-4 h-4" />
                            Reset password
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-slate-100 sticky top-0 bg-white">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Add New User</h2>
                <p className="text-sm text-slate-500">Create a new user for your institution</p>
              </div>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setError('');
                  setSuccess('');
                  setNewUser({
                    email: '',
                    password: '',
                    full_name: '',
                    role: 'counsellor',
                    phone: '',
                  });
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <form onSubmit={handleAddUser} className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {success && (
                <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center gap-2 text-green-700 text-sm">
                  <Check className="w-4 h-4 flex-shrink-0" />
                  {success}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Role
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['counsellor', 'student', 'admin'] as const).map((role) => {
                    const config = roleConfig[role];
                    const RoleIcon = config.icon;
                    return (
                      <button
                        key={role}
                        type="button"
                        onClick={() => setNewUser((prev) => ({ ...prev, role, assigned_counsellor_id: undefined }))}
                        className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all ${
                          newUser.role === role
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <RoleIcon className={`w-5 h-5 ${newUser.role === role ? 'text-indigo-600' : 'text-slate-400'}`} />
                        <span className={`text-sm font-medium ${newUser.role === role ? 'text-indigo-700' : 'text-slate-600'}`}>
                          {config.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {newUser.role === 'student' && counsellors.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Assign to Counsellor (optional)
                  </label>
                  <div className="relative">
                    <select
                      value={newUser.assigned_counsellor_id || ''}
                      onChange={(e) => setNewUser((prev) => ({ ...prev, assigned_counsellor_id: e.target.value || undefined }))}
                      className="w-full pl-4 pr-10 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all appearance-none bg-white"
                    >
                      <option value="">No assignment</option>
                      {counsellors.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.full_name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, full_name: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Dr. Jane Smith"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, email: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="jane.smith@institution.edu"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, password: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Minimum 8 characters"
                  required
                  minLength={8}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Phone (optional)
                </label>
                <input
                  type="tel"
                  value={newUser.phone}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, phone: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="+1-555-0123"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setError('');
                    setSuccess('');
                    setNewUser({
                      email: '',
                      password: '',
                      full_name: '',
                      role: 'counsellor',
                      phone: '',
                    });
                  }}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4" />
                      Create User
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && userForResetPassword && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Reset password</h2>
                <p className="text-sm text-slate-500">{userForResetPassword.full_name} ({userForResetPassword.email})</p>
              </div>
              <button
                onClick={() => {
                  setShowResetPasswordModal(false);
                  setUserForResetPassword(null);
                  setResetPasswordNew('');
                  setResetPasswordConfirm('');
                  setError('');
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <form onSubmit={handleResetPassword} className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}
              {success && (
                <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center gap-2 text-green-700 text-sm">
                  <Check className="w-4 h-4 flex-shrink-0" />
                  {success}
                </div>
              )}

              <p className="text-sm text-slate-600">
                Set a new password for this user. They can use it to login immediately.
              </p>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">New password</label>
                <input
                  type="password"
                  value={resetPasswordNew}
                  onChange={(e) => setResetPasswordNew(e.target.value)}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Minimum 8 characters"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Confirm password</label>
                <input
                  type="password"
                  value={resetPasswordConfirm}
                  onChange={(e) => setResetPasswordConfirm(e.target.value)}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Confirm new password"
                  required
                  minLength={8}
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowResetPasswordModal(false);
                    setUserForResetPassword(null);
                    setResetPasswordNew('');
                    setResetPasswordConfirm('');
                    setError('');
                  }}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isResettingPassword}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isResettingPassword ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Setting...
                    </>
                  ) : (
                    <>
                      <Key className="w-4 h-4" />
                      Set password
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Student Modal */}
      {showAssignModal && selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Assign Student to Counsellor</h2>
                <p className="text-sm text-slate-500">{selectedStudent.full_name}</p>
              </div>
              <button
                onClick={() => {
                  setShowAssignModal(false);
                  setSelectedStudent(null);
                  setSelectedCounsellorId('');
                  setError('');
                  setSuccess('');
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {success && (
                <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center gap-2 text-green-700 text-sm">
                  <Check className="w-4 h-4 flex-shrink-0" />
                  {success}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Select Counsellor (Max 10 students per counsellor)
                </label>
                <div className="relative">
                  <select
                    value={selectedCounsellorId}
                    onChange={(e) => setSelectedCounsellorId(e.target.value)}
                    className="w-full pl-4 pr-10 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all appearance-none bg-white"
                  >
                    <option value="">Unassign (no counsellor)</option>
                    {counsellors.map((c) => {
                      const assignedCount = users.filter(
                        (u) => u.role === 'student' && u.assigned_counsellor_id === c.id && u.is_active
                      ).length;
                      const isAtCapacity = assignedCount >= 10;
                      const willBeAtCapacity = selectedStudent.assigned_counsellor_id !== c.id && assignedCount >= 10;
                      return (
                        <option 
                          key={c.id} 
                          value={c.id}
                          disabled={willBeAtCapacity}
                        >
                          {c.full_name} ({assignedCount}/10 students)
                          {isAtCapacity && ' [FULL]'}
                        </option>
                      );
                    })}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                </div>
                {counsellors.length === 0 && (
                  <p className="mt-2 text-sm text-amber-600">
                    No active counsellors available. Create a counsellor first.
                  </p>
                )}
                {selectedCounsellorId && (
                  (() => {
                    const selectedCounsellor = counsellors.find(c => c.id === selectedCounsellorId);
                    const assignedCount = selectedCounsellor 
                      ? users.filter(
                          (u) => u.role === 'student' && u.assigned_counsellor_id === selectedCounsellorId && u.is_active && u.id !== selectedStudent.id
                        ).length
                      : 0;
                    const isAtCapacity = assignedCount >= 10;
                    return isAtCapacity ? (
                      <p className="mt-2 text-sm text-red-600 font-medium">
                        ⚠️ This counsellor has reached maximum capacity (10 students). Please select another counsellor.
                      </p>
                    ) : (
                      <p className="mt-2 text-sm text-slate-600">
                        {selectedCounsellor?.full_name} currently has {assignedCount} assigned student{assignedCount !== 1 ? 's' : ''}. 
                        {assignedCount < 10 && ` (${10 - assignedCount} slot${10 - assignedCount !== 1 ? 's' : ''} remaining)`}
                      </p>
                    );
                  })()
                )}
              </div>

              {selectedStudent.assigned_counsellor_name && (
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-sm text-slate-600">
                    <span className="font-medium">Currently assigned to:</span>{' '}
                    {selectedStudent.assigned_counsellor_name}
                  </p>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAssignModal(false);
                    setSelectedStudent(null);
                    setSelectedCounsellorId('');
                    setError('');
                    setSuccess('');
                  }}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssignStudent}
                  disabled={isAssigning || counsellors.length === 0}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isAssigning ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Assigning...
                    </>
                  ) : (
                    <>
                      <UserCheck className="w-4 h-4" />
                      {selectedCounsellorId ? 'Assign' : 'Unassign'}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reassign Institution Modal */}
      {showReassignModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Reassign User to Institution</h2>
                <p className="text-sm text-slate-500">
                  {selectedUser.full_name} ({roleConfig[selectedUser.role].label})
                </p>
              </div>
              <button
                onClick={() => {
                  setShowReassignModal(false);
                  setSelectedUser(null);
                  setSelectedInstitutionId('');
                  setError('');
                  setSuccess('');
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {success && (
                <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center gap-2 text-green-700 text-sm">
                  <Check className="w-4 h-4 flex-shrink-0" />
                  {success}
                </div>
              )}

              <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                <p className="text-sm text-amber-800">
                  <strong>Warning:</strong> Reassigning a user to a different institution will move them to that institution's tenant. 
                  {selectedUser.role === 'student' && ' Any counsellor assignments will be cleared.'}
                  {(selectedUser.role === 'counsellor' || selectedUser.role === 'admin') && (
                    <span className="block mt-1 font-semibold text-red-700">
                      ⚠️ Only super admins can reassign admins or counsellors between institutions.
                    </span>
                  )}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Current Institution
                </label>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-sm text-slate-700 font-medium">{selectedUser.institution_name ?? '—'}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Select New Institution
                </label>
                <div className="relative">
                  <select
                    value={selectedInstitutionId}
                    onChange={(e) => setSelectedInstitutionId(e.target.value)}
                    className="w-full pl-4 pr-10 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all appearance-none bg-white"
                  >
                    <option value="">Select institution...</option>
                    {institutions
                      .filter((inst) => inst.id !== selectedUser.institution_id && inst.is_active)
                      .map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.name}
                        </option>
                      ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                </div>
                {institutions.filter((inst) => inst.id !== selectedUser.institution_id && inst.is_active).length === 0 && (
                  <p className="mt-2 text-sm text-amber-600">
                    No other active institutions available.
                  </p>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowReassignModal(false);
                    setSelectedUser(null);
                    setSelectedInstitutionId('');
                    setError('');
                    setSuccess('');
                  }}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReassignInstitution}
                  disabled={isReassigning || !selectedInstitutionId || selectedInstitutionId === selectedUser.institution_id}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isReassigning ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Reassigning...
                    </>
                  ) : (
                    <>
                      <ArrowRightLeft className="w-4 h-4" />
                      Reassign
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
