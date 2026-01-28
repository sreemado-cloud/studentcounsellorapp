import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  passwordResetRequired: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, fullName: string, institutionId: string) => Promise<boolean>;
  logout: () => void;
  resetPassword: (currentPassword: string, newPassword: string) => Promise<void>;
  clearPasswordResetRequired: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [passwordResetRequired, setPasswordResetRequired] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');

    if (savedToken && savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setToken(savedToken);
      setUser(parsedUser);
      setPasswordResetRequired(parsedUser.password_reset_required || false);

      // Refresh user from /me so we have up-to-date fields (e.g. is_super_admin)
      authApi
        .getMe()
        .then((me) => {
          setUser(me);
          setPasswordResetRequired(me.password_reset_required ?? false);
          localStorage.setItem('user', JSON.stringify(me));
        })
        .catch(() => {
          setToken(null);
          setUser(null);
          setPasswordResetRequired(false);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    const response = await authApi.login(email, password);
    const t = response.access_token ?? null;
    const u = response.user ?? null;
    setToken(t);
    setUser(u);
    const resetRequired = response.password_reset_required ?? u?.password_reset_required ?? false;
    setPasswordResetRequired(resetRequired);
    if (t) localStorage.setItem('token', t);
    if (u) localStorage.setItem('user', JSON.stringify(u));
    return resetRequired;
  };

  const register = async (email: string, password: string, fullName: string, institutionId: string): Promise<boolean> => {
    const response = await authApi.register({
      email,
      password,
      full_name: fullName,
      institution_id: institutionId,
    });
    
    // Check if registration requires approval (for students)
    if (response.requires_approval) {
      // Don't set token/user - student needs approval
      return false; // No password reset required since they can't login yet
    }
    
    const t = response.access_token ?? null;
    const u = response.user ?? null;
    setToken(t);
    setUser(u);
    const resetRequired = response.password_reset_required ?? u?.password_reset_required ?? false;
    setPasswordResetRequired(resetRequired);
    if (t) localStorage.setItem('token', t);
    if (u) localStorage.setItem('user', JSON.stringify(u));
    return resetRequired;
  };

  const resetPassword = async (currentPassword: string, newPassword: string) => {
    await authApi.resetPassword(currentPassword, newPassword);
    if (user) {
      const updatedUser = { ...user, password_reset_required: false };
      setUser(updatedUser);
      setPasswordResetRequired(false);
      localStorage.setItem('user', JSON.stringify(updatedUser));
    } else {
      setPasswordResetRequired(false);
    }
  };

  const clearPasswordResetRequired = () => {
    setPasswordResetRequired(false);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setPasswordResetRequired(false);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      isLoading, 
      passwordResetRequired,
      login, 
      register, 
      logout,
      resetPassword,
      clearPasswordResetRequired
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
