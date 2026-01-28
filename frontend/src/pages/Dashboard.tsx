import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { appointmentsApi, messagesApi } from '../services/api';
import type { Appointment, Conversation } from '../types';
import { format } from 'date-fns';
import {
  Calendar,
  MessageSquare,
  Clock,
  ArrowRight,
  Sparkles,
  TrendingUp,
  CheckCircle,
  Building2,
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appointmentsData, conversationsData] = await Promise.all([
          appointmentsApi.getAll(),
          messagesApi.getConversations(),
        ]);
        setAppointments(appointmentsData.slice(0, 3));
        setConversations(conversationsData.slice(0, 3));
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const upcomingAppointments = appointments.filter(
    (apt) => apt.status === 'pending' || apt.status === 'confirmed'
  );

  const totalUnread = conversations.reduce((acc, conv) => acc + conv.unread_count, 0);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-700';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'completed':
        return 'bg-blue-100 text-blue-700';
      case 'cancelled':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-indigo-100 mb-1">{getGreeting()},</p>
            <h1 className="text-3xl font-bold mb-2">{user?.full_name}</h1>
            {user?.institution_name && (
              <p className="text-indigo-100 flex items-center gap-2 mb-2">
                <Building2 className="w-4 h-4" />
                {user.institution_name}
              </p>
            )}
            <p className="text-indigo-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Welcome to your personalized counselling dashboard
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-24 h-24 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <span className="text-4xl font-bold">{user?.full_name?.charAt(0)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-indigo-100 flex items-center justify-center">
              <Calendar className="w-7 h-7 text-indigo-600" />
            </div>
            <div>
              <p className="text-slate-500 text-sm">Upcoming Sessions</p>
              <p className="text-2xl font-bold text-slate-800">{upcomingAppointments.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-purple-100 flex items-center justify-center">
              <MessageSquare className="w-7 h-7 text-purple-600" />
            </div>
            <div>
              <p className="text-slate-500 text-sm">Unread Messages</p>
              <p className="text-2xl font-bold text-slate-800">{totalUnread}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-green-100 flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-green-600" />
            </div>
            <div>
              <p className="text-slate-500 text-sm">Total Sessions</p>
              <p className="text-2xl font-bold text-slate-800">{appointments.length}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Appointments */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100">
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">Upcoming Appointments</h2>
              <Link
                to="/appointments"
                className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center gap-1"
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
                <Link
                  to="/appointments"
                  className="mt-4 inline-flex items-center gap-2 text-indigo-600 font-medium"
                >
                  Book a session <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {upcomingAppointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate">{apt.title}</p>
                      <p className="text-sm text-slate-500 flex items-center gap-2">
                        <Clock className="w-3 h-3" />
                        {format(new Date(apt.date), 'MMM d, yyyy h:mm a')}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(apt.status)}`}>
                      {apt.status}
                    </span>
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
              <h2 className="text-lg font-semibold text-slate-800">Recent Conversations</h2>
              <Link
                to="/messages"
                className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="p-6">
            {conversations.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No conversations yet</p>
                <Link
                  to="/messages"
                  className="mt-4 inline-flex items-center gap-2 text-indigo-600 font-medium"
                >
                  Start a conversation <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {conversations.map((conv) => (
                  <div
                    key={conv.participant_id}
                    className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                      {conv.participant_name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate">{conv.participant_name}</p>
                      <p className="text-sm text-slate-500 truncate">{conv.last_message}</p>
                    </div>
                    {conv.unread_count > 0 && (
                      <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Tips */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-100">
        <h3 className="font-semibold text-amber-800 flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5" />
          Quick Tips for Success
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <p className="text-sm text-amber-800">Schedule regular check-ins with your counsellor</p>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <p className="text-sm text-amber-800">Keep notes of your goals and progress</p>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <p className="text-sm text-amber-800">Don't hesitate to ask questions</p>
          </div>
        </div>
      </div>
    </div>
  );
}
