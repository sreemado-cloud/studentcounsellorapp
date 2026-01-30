import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { appointmentsApi, messagesApi, institutionsApi } from '../services/api';
import type { Appointment, Conversation } from '../types';
import {
  Calendar,
  MessageSquare,
  Users,
  Clock,
  CheckCircle,
  ArrowRight,
  Building2,
} from 'lucide-react';
import { format, parseISO, isAfter } from 'date-fns';

export default function CounsellorDashboard() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [stats, setStats] = useState({
    totalStudents: 0,
    totalCounsellors: 0,
    totalAppointments: 0,
    totalMessages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appointmentsData, conversationsData, statsData] = await Promise.all([
          appointmentsApi.getAll(),
          messagesApi.getConversations(),
          institutionsApi.getStats(),
        ]);
        
        setAppointments(appointmentsData);
        setConversations(conversationsData);
        setStats({
          totalStudents: statsData.total_students,
          totalCounsellors: statsData.total_counsellors,
          totalAppointments: statsData.total_appointments,
          totalMessages: statsData.total_messages,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // Filter upcoming appointments
  const upcomingAppointments = appointments
    .filter((apt) => {
      const aptDate = parseISO(apt.date);
      return isAfter(aptDate, new Date()) && apt.status !== 'cancelled';
    })
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(0, 5);

  // Get pending appointments count
  const pendingCount = appointments.filter((apt) => apt.status === 'pending').length;
  
  // Get unread messages count
  const unreadCount = conversations.reduce((acc, conv) => acc + conv.unread_count, 0);

  const handleConfirmAppointment = async (id: string) => {
    try {
      await appointmentsApi.update(id, { status: 'confirmed' });
      setAppointments((prev) =>
        prev.map((apt) => (apt.id === id ? { ...apt, status: 'confirmed' } : apt))
      );
    } catch (error) {
      console.error('Failed to confirm appointment:', error);
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800">
          Welcome back, {user?.full_name?.split(' ')[0]}!
        </h1>
        <div className="flex items-center gap-2 mt-2 text-slate-600">
          <Building2 className="w-4 h-4" />
          <span>{user?.institution_name || 'Your Institution'}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center">
              <Clock className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{pendingCount}</p>
              <p className="text-sm text-slate-500">Pending Appointments</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{unreadCount}</p>
              <p className="text-sm text-slate-500">Unread Messages</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{stats.totalStudents}</p>
              <p className="text-sm text-slate-500">Total Students</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{stats.totalAppointments}</p>
              <p className="text-sm text-slate-500">Total Appointments</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Appointments */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100">
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">Upcoming Appointments</h2>
              <Link
                to="/appointments"
                className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="p-6">
            {upcomingAppointments.length === 0 ? (
              <div className="text-center py-8">
                <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No upcoming appointments</p>
              </div>
            ) : (
              <div className="space-y-4">
                {upcomingAppointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-xl"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate">
                        {apt.student_name}
                      </p>
                      <p className="text-sm text-slate-500">
                        {format(parseISO(apt.date), 'MMM d, yyyy • h:mm a')}
                      </p>
                      <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 mt-1">
                        {apt.appointment_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {apt.status === 'pending' ? (
                        <button
                          onClick={() => handleConfirmAppointment(apt.id)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
                        >
                          <CheckCircle className="w-4 h-4" />
                          Confirm
                        </button>
                      ) : (
                        <span className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-sm">
                          <CheckCircle className="w-4 h-4" />
                          Confirmed
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Messages */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100">
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">Recent Messages</h2>
              <Link
                to="/messages"
                className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="p-6">
            {conversations.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No messages yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {conversations.slice(0, 5).map((conv) => (
                  <Link
                    key={conv.participant_id}
                    to="/messages"
                    className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                      {conv.participant_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-slate-800 truncate">
                          {conv.participant_name}
                        </p>
                        {conv.unread_count > 0 && (
                          <span className="w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 truncate">{conv.last_message}</p>
                    </div>
                    <span className="text-xs text-slate-400">
                      {format(parseISO(conv.last_message_time), 'MMM d')}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            to="/students"
            className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors"
          >
            <Users className="w-6 h-6 text-blue-600" />
            <span className="font-medium text-blue-700">View All Students</span>
          </Link>
          <Link
            to="/appointments"
            className="flex items-center gap-3 p-4 bg-amber-50 rounded-xl hover:bg-amber-100 transition-colors"
          >
            <Calendar className="w-6 h-6 text-amber-600" />
            <span className="font-medium text-amber-700">Manage Appointments</span>
          </Link>
          <Link
            to="/messages"
            className="flex items-center gap-3 p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-colors"
          >
            <MessageSquare className="w-6 h-6 text-purple-600" />
            <span className="font-medium text-purple-700">View Messages</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
