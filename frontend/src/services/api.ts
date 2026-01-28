import axios from 'axios';
import type { AuthResponse, User, Appointment, Message, Conversation, Note, Institution } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Institutions
export const institutionsApi = {
  getAll: async (): Promise<Institution[]> => {
    const response = await api.get('/institutions/');
    return response.data;
  },

  get: async (id: string): Promise<Institution> => {
    const response = await api.get(`/institutions/${id}`);
    return response.data;
  },

  getCurrent: async (): Promise<Institution> => {
    const response = await api.get('/institutions/current');
    return response.data;
  },

  getStats: async (): Promise<{
    institution_id: string;
    total_students: number;
    total_counsellors: number;
    total_appointments: number;
    total_messages: number;
  }> => {
    const response = await api.get('/institutions/current/stats');
    return response.data;
  },

  getUsers: async (role?: string, includeInactive?: boolean): Promise<User[]> => {
    const params: Record<string, string | boolean> = {};
    if (role) params.role = role;
    if (includeInactive) params.include_inactive = true;
    const response = await api.get('/institutions/current/users', { params });
    return response.data;
  },
};

// Auth
export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
    institution_id: string;
    role?: string;
  }): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  resetPassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/auth/reset-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },

  resetPasswordWithToken: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await api.post('/auth/reset-password-with-token', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Users
export const usersApi = {
  getCounsellors: async (): Promise<User[]> => {
    const response = await api.get('/users/counsellors');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.put('/users/me', data);
    return response.data;
  },

  getUser: async (userId: string): Promise<User> => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },
};

// Appointments
export const appointmentsApi = {
  create: async (data: {
    counsellor_id: string;
    date: string;
    duration_minutes: number;
    appointment_type: string;
    title: string;
    description?: string;
  }): Promise<Appointment> => {
    const response = await api.post('/appointments/', data);
    return response.data;
  },

  getAll: async (status?: string): Promise<Appointment[]> => {
    const params = status ? { status } : {};
    const response = await api.get('/appointments/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Appointment> => {
    const response = await api.get(`/appointments/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Appointment>): Promise<Appointment> => {
    const response = await api.put(`/appointments/${id}`, data);
    return response.data;
  },

  cancel: async (id: string): Promise<void> => {
    await api.delete(`/appointments/${id}`);
  },
};

// Messages
export const messagesApi = {
  send: async (data: {
    recipient_id: string;
    content: string;
    subject?: string;
  }): Promise<Message> => {
    const response = await api.post('/messages/', data);
    return response.data;
  },

  getAll: async (): Promise<Message[]> => {
    const response = await api.get('/messages/');
    return response.data;
  },

  getConversations: async (): Promise<Conversation[]> => {
    const response = await api.get('/messages/conversations');
    return response.data;
  },

  markAsRead: async (id: string): Promise<Message> => {
    const response = await api.put(`/messages/${id}/read`);
    return response.data;
  },
};

// Notes
export const notesApi = {
  create: async (data: {
    title: string;
    content: string;
    category: string;
    tags?: string[];
    is_private?: boolean;
  }): Promise<Note> => {
    const response = await api.post('/notes/', data);
    return response.data;
  },

  getAll: async (category?: string, search?: string): Promise<Note[]> => {
    const params: Record<string, string> = {};
    if (category) params.category = category;
    if (search) params.search = search;
    const response = await api.get('/notes/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Note> => {
    const response = await api.get(`/notes/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Note>): Promise<Note> => {
    const response = await api.put(`/notes/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/notes/${id}`);
  },
};

// Admin
export const adminApi = {
  approveStudent: async (userId: string): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/approve`);
    return response.data;
  },

  rejectStudent: async (userId: string, reason?: string): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/reject`, { reason });
    return response.data;
  },

  updateUserStatus: async (userId: string, isActive: boolean): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/status`, null, {
      params: { is_active: isActive },
    });
    return response.data;
  },

  setUserPassword: async (userId: string, newPassword: string): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/set-password`, {
      new_password: newPassword,
    });
    return response.data;
  },
};

export default api;
