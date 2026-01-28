export type UserRole = 'student' | 'counsellor' | 'admin';

// Institution (Tenant) types
export interface InstitutionSettings {
  branding_color: string;
  logo_url?: string;
  max_counsellors: number;
  max_students: number;
  features_enabled: string[];
  custom_domain?: string;
}

export interface Institution {
  id: string;
  name: string;
  domain?: string;
  subscription_tier: 'free' | 'basic' | 'professional' | 'enterprise';
  settings: InstitutionSettings;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  user_count?: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id: string;
  institution_name?: string;
  assigned_counsellor_id?: string;
  assigned_counsellor_name?: string;
  phone?: string;
  grade?: string;
  major?: string;
  bio?: string;
  profile_image?: string;
  created_at: string;
  is_active: boolean;
  password_reset_required?: boolean;
  approval_status?: 'pending' | 'approved' | 'rejected';
  is_super_admin?: boolean;
}

export interface AuthResponse {
  access_token?: string;
  token_type?: string;
  user?: User;
  password_reset_required?: boolean;
  requires_approval?: boolean;
  message?: string;
}

// Student info for counsellors
export interface StudentInfo {
  id: string;
  email: string;
  full_name: string;
  grade?: string;
  major?: string;
  created_at: string;
  appointment_count?: number;
  last_appointment?: string;
}

export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled';
export type AppointmentType = 'academic' | 'career' | 'personal' | 'mental_health' | 'other';

export interface Appointment {
  id: string;
  student_id: string;
  student_name?: string;
  counsellor_id: string;
  counsellor_name?: string;
  date: string;
  duration_minutes: number;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  title: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  sender_id: string;
  sender_name: string;
  recipient_id: string;
  recipient_name: string;
  subject?: string;
  content: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
  student_id: string;
}

export interface Conversation {
  participant_id: string;
  participant_name: string;
  participant_role: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

export type NoteCategory = 'general' | 'academic' | 'career' | 'personal' | 'goals' | 'resources';

export interface Note {
  id: string;
  student_id: string;
  title: string;
  content: string;
  category: NoteCategory;
  tags: string[];
  is_private: boolean;
  created_at: string;
  updated_at?: string;
}
