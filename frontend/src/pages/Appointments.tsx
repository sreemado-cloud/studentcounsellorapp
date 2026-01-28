import { useEffect, useState } from 'react';
import { appointmentsApi, usersApi } from '../services/api';
import type { Appointment, User } from '../types';
import { format } from 'date-fns';
import {
  Calendar,
  Clock,
  Plus,
  X,
  AlertCircle,
  User as UserIcon,
} from 'lucide-react';

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [counsellors, setCounsellors] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  // Form state
  const [selectedCounsellor, setSelectedCounsellor] = useState('');
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentTime, setAppointmentTime] = useState('');
  const [appointmentType, setAppointmentType] = useState('academic');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [appointmentsData, counsellorsData] = await Promise.all([
        appointmentsApi.getAll(),
        usersApi.getCounsellors(),
      ]);
      setAppointments(appointmentsData);
      setCounsellors(counsellorsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const dateTime = new Date(`${appointmentDate}T${appointmentTime}`);
      await appointmentsApi.create({
        counsellor_id: selectedCounsellor,
        date: dateTime.toISOString(),
        duration_minutes: 30,
        appointment_type: appointmentType,
        title,
        description,
      });
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to create appointment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async (id: string) => {
    if (confirm('Are you sure you want to cancel this appointment?')) {
      try {
        await appointmentsApi.cancel(id);
        fetchData();
      } catch (error) {
        console.error('Error cancelling appointment:', error);
      }
    }
  };

  const resetForm = () => {
    setSelectedCounsellor('');
    setAppointmentDate('');
    setAppointmentTime('');
    setAppointmentType('academic');
    setTitle('');
    setDescription('');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'completed':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'cancelled':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'academic':
        return 'bg-blue-500';
      case 'career':
        return 'bg-purple-500';
      case 'personal':
        return 'bg-pink-500';
      case 'mental_health':
        return 'bg-green-500';
      default:
        return 'bg-slate-500';
    }
  };

  const filteredAppointments = appointments.filter((apt) => {
    if (filter === 'all') return true;
    return apt.status === filter;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Appointments</h1>
          <p className="text-slate-500">Manage your counselling sessions</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all"
        >
          <Plus className="w-5 h-5" />
          Book Appointment
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
              filter === status
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Appointments List */}
      {filteredAppointments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
          <Calendar className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">No appointments found</h3>
          <p className="text-slate-500 mb-4">
            {filter === 'all'
              ? "You haven't booked any appointments yet"
              : `No ${filter} appointments`}
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 text-indigo-600 font-medium"
          >
            <Plus className="w-4 h-4" />
            Book your first appointment
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredAppointments.map((apt) => (
            <div
              key={apt.id}
              className="bg-white rounded-2xl p-6 border border-slate-100 hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-center gap-4">
                <div className={`w-2 h-full md:w-1 md:h-20 rounded-full ${getTypeColor(apt.appointment_type)}`} />
                
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-slate-800 text-lg">{apt.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(apt.status)}`}>
                      {apt.status}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(apt.date), 'EEEE, MMMM d, yyyy')}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {format(new Date(apt.date), 'h:mm a')} ({apt.duration_minutes} min)
                    </span>
                    <span className="flex items-center gap-1">
                      <UserIcon className="w-4 h-4" />
                      {apt.counsellor_name}
                    </span>
                  </div>
                  
                  {apt.description && (
                    <p className="mt-2 text-slate-600">{apt.description}</p>
                  )}
                </div>

                {(apt.status === 'pending' || apt.status === 'confirmed') && (
                  <button
                    onClick={() => handleCancel(apt.id)}
                    className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-800">Book Appointment</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {error && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  <p className="text-sm">{error}</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Select Counsellor
                </label>
                <select
                  value={selectedCounsellor}
                  onChange={(e) => setSelectedCounsellor(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="">Choose a counsellor</option>
                  {counsellors.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Date
                  </label>
                  <input
                    type="date"
                    value={appointmentDate}
                    onChange={(e) => setAppointmentDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Time
                  </label>
                  <input
                    type="time"
                    value={appointmentTime}
                    onChange={(e) => setAppointmentTime(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Appointment Type
                </label>
                <select
                  value={appointmentType}
                  onChange={(e) => setAppointmentType(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="academic">Academic Counselling</option>
                  <option value="career">Career Guidance</option>
                  <option value="personal">Personal Development</option>
                  <option value="mental_health">Mental Health Support</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Brief title for your appointment"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                  placeholder="What would you like to discuss?"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-3 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Booking...' : 'Book Appointment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
