import { useState } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Calendar,
  MessageSquare,
  FileText,
  User,
  LogOut,
  Menu,
  X,
  GraduationCap,
  Users,
  Building2,
  Settings,
  Shield,
} from 'lucide-react';
import type { UserRole } from '../types';

interface LayoutProps {
  children: ReactNode;
}

interface NavItem {
  path: string;
  icon: typeof LayoutDashboard;
  label: string;
  roles: UserRole[];
  superAdminOnly?: boolean;
}

// Navigation items with role-based access
const navItems: NavItem[] = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['student', 'counsellor', 'admin'] },
  { path: '/students', icon: Users, label: 'My Students', roles: ['counsellor', 'admin'] },
  { path: '/appointments', icon: Calendar, label: 'Appointments', roles: ['student', 'counsellor', 'admin'] },
  { path: '/messages', icon: MessageSquare, label: 'Messages', roles: ['student', 'counsellor', 'admin'] },
  { path: '/notes', icon: FileText, label: 'My Notes', roles: ['student'] },
  { path: '/admin', icon: Settings, label: 'Admin Panel', roles: ['admin'] },
  { path: '/institutions', icon: Building2, label: 'Institutions', roles: ['admin'] },
  { path: '/super-admin', icon: Shield, label: 'Super Admin', roles: ['admin'], superAdminOnly: true },
  { path: '/profile', icon: User, label: 'Profile', roles: ['student', 'counsellor', 'admin'] },
];

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Filter navigation items based on user role and super-admin-only
  const filteredNavItems = navItems.filter((item) => {
    if (item.superAdminOnly) return !!user?.is_super_admin;
    return !!user?.role && item.roles.includes(user.role);
  });

  // Get role display name and color
  const getRoleDisplay = (role?: UserRole) => {
    switch (role) {
      case 'counsellor':
        return { name: 'Counsellor', color: 'text-emerald-600 bg-emerald-50' };
      case 'admin':
        return { name: 'Admin', color: 'text-purple-600 bg-purple-50' };
      default:
        return { name: 'Student', color: 'text-blue-600 bg-blue-50' };
    }
  };

  const roleDisplay = getRoleDisplay(user?.role);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-8 h-8 text-indigo-600" />
          <span className="font-bold text-xl text-slate-800">StudentCounsellor</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg hover:bg-slate-100"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-screen w-72 bg-white border-r border-slate-200 transition-transform lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="hidden lg:flex items-center gap-3 px-6 py-5 border-b border-slate-200">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-800">StudentCounsellor</h1>
              <p className="text-xs text-slate-500">Your academic partner</p>
            </div>
          </div>

          {/* User info */}
          <div className="px-4 py-4 mt-16 lg:mt-0">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold text-lg">
                  {user?.full_name?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800 truncate">{user?.full_name}</p>
                  <span className={`inline-block text-xs px-2 py-0.5 rounded-full ${roleDisplay.color}`}>
                    {roleDisplay.name}
                  </span>
                </div>
              </div>
              {/* Institution name */}
              {user?.institution_name && (
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-600">
                  <Building2 className="w-3.5 h-3.5" />
                  <span className="truncate">{user.institution_name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-2">
            <ul className="space-y-1">
              {filteredNavItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-slate-200">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="lg:ml-72 pt-16 lg:pt-0 min-h-screen">
        <div className="p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
