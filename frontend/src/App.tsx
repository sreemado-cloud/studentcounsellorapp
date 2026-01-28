import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import PasswordResetModal from './components/PasswordResetModal';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import CounsellorDashboard from './pages/CounsellorDashboard';
import Appointments from './pages/Appointments';
import CounsellorAppointments from './pages/CounsellorAppointments';
import Messages from './pages/Messages';
import Notes from './pages/Notes';
import Profile from './pages/Profile';
import Students from './pages/Students';
import AdminPanel from './pages/AdminPanel';
import SuperAdminPage from './pages/SuperAdminPage';
import type { UserRole } from './types';

const queryClient = new QueryClient();

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check role-based access
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Layout>{children}</Layout>;
}

function SuperAdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!user.is_super_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Layout>{children}</Layout>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

// Dashboard wrapper that renders the appropriate dashboard based on role
function DashboardWrapper() {
  const { user } = useAuth();

  if (user?.role === 'counsellor' || user?.role === 'admin') {
    return <CounsellorDashboard />;
  }

  return <Dashboard />;
}

// Appointments wrapper that renders the appropriate view based on role
function AppointmentsWrapper() {
  const { user } = useAuth();

  if (user?.role === 'counsellor' || user?.role === 'admin') {
    return <CounsellorAppointments />;
  }

  return <Appointments />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <ForgotPassword />
          </PublicRoute>
        }
      />
      <Route
        path="/reset-password"
        element={
          <PublicRoute>
            <ResetPassword />
          </PublicRoute>
        }
      />

      {/* Protected routes - All roles */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardWrapper />
          </ProtectedRoute>
        }
      />
      <Route
        path="/appointments"
        element={
          <ProtectedRoute>
            <AppointmentsWrapper />
          </ProtectedRoute>
        }
      />
      <Route
        path="/messages"
        element={
          <ProtectedRoute>
            <Messages />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />

      {/* Student only routes */}
      <Route
        path="/notes"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <Notes />
          </ProtectedRoute>
        }
      />

      {/* Counsellor and Admin only routes */}
      <Route
        path="/students"
        element={
          <ProtectedRoute allowedRoles={['counsellor', 'admin']}>
            <Students />
          </ProtectedRoute>
        }
      />

      {/* Admin only routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminPanel />
          </ProtectedRoute>
        }
      />

      {/* Super Admin only: view and disable admins */}
      <Route
        path="/super-admin"
        element={
          <SuperAdminRoute>
            <SuperAdminPage />
          </SuperAdminRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function AppWithModal() {
  return (
    <>
      <AppRoutes />
      <PasswordResetModal />
    </>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppWithModal />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
