import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usersApi } from '../services/api';
import {
  User,
  Mail,
  Phone,
  BookOpen,
  GraduationCap,
  Save,
  CheckCircle,
  Key,
  AlertCircle,
} from 'lucide-react';

export default function Profile() {
  const { user, resetPassword } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [grade, setGrade] = useState(user?.grade || '');
  const [major, setMajor] = useState(user?.major || '');
  const [bio, setBio] = useState(user?.bio || '');

  const [showChangePassword, setShowChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await usersApi.updateProfile({
        full_name: fullName,
        phone,
        grade,
        major,
        bio,
      });
      setIsEditing(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    setIsChangingPassword(true);
    try {
      await resetPassword(currentPassword, newPassword);
      setPasswordSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowChangePassword(false);
      setTimeout(() => setPasswordSuccess(''), 3000);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setPasswordError(ax.response?.data?.detail ?? 'Failed to change password. Check current password.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Profile</h1>
        <p className="text-slate-500">Manage your account information</p>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <div className="p-4 bg-green-50 border border-green-100 rounded-xl flex items-center gap-3 text-green-700">
          <CheckCircle className="w-5 h-5" />
          <p className="font-medium">Profile updated successfully!</p>
        </div>
      )}

      {/* Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        {/* Banner */}
        <div className="h-32 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

        {/* Avatar & Actions */}
        <div className="px-6 pb-6">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between -mt-12 mb-6">
            <div className="flex items-end gap-4">
              <div className="w-24 h-24 rounded-2xl bg-white shadow-lg flex items-center justify-center border-4 border-white">
                <span className="text-4xl font-bold text-indigo-600">
                  {user?.full_name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="pb-2">
                <h2 className="text-xl font-bold text-slate-800">{user?.full_name}</h2>
                <p className="text-slate-500 capitalize">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
              disabled={isSaving}
              className="mt-4 sm:mt-0 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all disabled:opacity-50"
            >
              {isSaving ? (
                'Saving...'
              ) : isEditing ? (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              ) : (
                'Edit Profile'
              )}
            </button>
          </div>

          {/* Form */}
          <div className="grid gap-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <span className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Full Name
                  </span>
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <span className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Email
                  </span>
                </label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl bg-slate-50 text-slate-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <span className="flex items-center gap-2">
                    <Phone className="w-4 h-4" />
                    Phone
                  </span>
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={!isEditing}
                  placeholder="Enter your phone number"
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <span className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4" />
                    Grade/Year
                  </span>
                </label>
                <input
                  type="text"
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  disabled={!isEditing}
                  placeholder="e.g., Junior, Senior, 3rd Year"
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  Major/Field of Study
                </span>
              </label>
              <input
                type="text"
                value={major}
                onChange={(e) => setMajor(e.target.value)}
                disabled={!isEditing}
                placeholder="e.g., Computer Science, Business Administration"
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-50 disabled:text-slate-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                disabled={!isEditing}
                rows={4}
                placeholder="Tell us a bit about yourself..."
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-50 disabled:text-slate-500 resize-none"
              />
            </div>

            {isEditing && (
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setFullName(user?.full_name || '');
                    setPhone(user?.phone || '');
                    setGrade(user?.grade || '');
                    setMajor(user?.major || '');
                    setBio(user?.bio || '');
                  }}
                  className="px-4 py-2 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Account Info */}
      <div className="bg-white rounded-2xl border border-slate-100 p-6">
        <h3 className="font-semibold text-slate-800 mb-4">Account Information</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Account Type</span>
            <span className="font-medium text-slate-800 capitalize">{user?.role}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Member Since</span>
            <span className="font-medium text-slate-800">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('en-US', {
                    month: 'long',
                    year: 'numeric',
                  })
                : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-slate-500">Account Status</span>
            <span className="inline-flex items-center gap-1 text-green-600 font-medium">
              <CheckCircle className="w-4 h-4" />
              Active
            </span>
          </div>
        </div>
      </div>

      {/* Change password */}
      <div className="bg-white rounded-2xl border border-slate-100 p-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="font-semibold text-slate-800">Password</h3>
          {!showChangePassword ? (
            <button
              type="button"
              onClick={() => {
                setShowChangePassword(true);
                setPasswordError('');
                setPasswordSuccess('');
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
              }}
              className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-medium underline underline-offset-2"
            >
              <Key className="w-4 h-4" />
              Change password
            </button>
          ) : null}
        </div>
        {showChangePassword && (
          <form onSubmit={handleChangePassword} className="mt-4 space-y-4">
            {passwordError && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-2 text-red-700 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {passwordError}
              </div>
            )}
            {passwordSuccess && (
              <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center gap-2 text-green-700 text-sm">
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
                {passwordSuccess}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Current password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter current password"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">New password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Min. 8 characters"
                required
                minLength={8}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Confirm new password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Confirm new password"
                required
                minLength={8}
              />
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowChangePassword(false);
                  setPasswordError('');
                  setPasswordSuccess('');
                  setCurrentPassword('');
                  setNewPassword('');
                  setConfirmPassword('');
                }}
                className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-xl font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isChangingPassword}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isChangingPassword ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Updating...
                  </>
                ) : (
                  <>
                    <Key className="w-4 h-4" />
                    Update password
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
