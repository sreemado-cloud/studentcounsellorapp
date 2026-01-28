import { useState, useEffect } from 'react';
import { appointmentsApi } from '../services/api';
import type { Appointment, AppointmentStatus } from '../types';
import {
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Filter,
  FileText,
  X,
} from 'lucide-react';
import { format, parseISO, isAfter, isBefore } from 'date-fns';

const statusColors: Record<AppointmentStatus, string> = {
  pending: 'bg-amber-100 text-amber-700',
  confirmed: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

const statusIcons: Record<AppointmentStatus, typeof Clock> = {
  pending: Clock,
  confirmed: CheckCircle,
  completed: CheckCircle,
  cancelled: XCircle,
};

export default function CounsellorAppointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<AppointmentStatus | 'all' | 'upcoming'>('upcoming');
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [notes, setNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const data = await appointmentsApi.getAll();
      setAppointments(data);
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusUpdate = async (id: string, status: AppointmentStatus) => {
    setIsUpdating(true);
    try {
      await appointmentsApi.update(id, { status });
      setAppointments((prev) =>
        prev.map((apt) => (apt.id === id ? { ...apt, status } : apt))
      );
    } catch (error) {
      console.error('Failed to update appointment:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAddNotes = async () => {
    if (!selectedAppointment) return;
    setIsUpdating(true);
    try {
      await appointmentsApi.update(selectedAppointment.id, { notes });
      setAppointments((prev) =>
        prev.map((apt) =>
          apt.id === selectedAppointment.id ? { ...apt, notes } : apt
        )
      );
      setShowNotesModal(false);
      setSelectedAppointment(null);
      setNotes('');
    } catch (error) {
      console.error('Failed to add notes:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const openNotesModal = (apt: Appointment) => {
    setSelectedAppointment(apt);
    setNotes(apt.notes || '');
    setShowNotesModal(true);
  };

  // Filter appointments
  const filteredAppointments = appointments.filter((apt) => {
    if (filter === 'all') return true;
    if (filter === 'upcoming') {
      const aptDate = parseISO(apt.date);
      return isAfter(aptDate, new Date()) && apt.status !== 'cancelled';
    }
    return apt.status === filter;
  });

  // Sort by date
  const sortedAppointments = [...filteredAppointments].sort((a, b) => {
    return new Date(a.date).getTime() - new Date(b.date).getTime();
  });

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
          <h1 className="text-3xl font-bold text-slate-800">Appointments</h1>
          <p className="text-slate-600 mt-1">Manage your counselling sessions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <Filter className="w-5 h-5 text-slate-400 flex-shrink-0" />
          {(['upcoming', 'all', 'pending', 'confirmed', 'completed', 'cancelled'] as const).map(
            (status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  filter === status
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            )
          )}
        </div>
      </div>

      {/* Appointments List */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100">
        {sortedAppointments.length === 0 ? (
          <div className="text-center py-12">
            <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No appointments found</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {sortedAppointments.map((apt) => {
              const StatusIcon = statusIcons[apt.status];
              const isPast = isBefore(parseISO(apt.date), new Date());
              
              return (
                <div key={apt.id} className="p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    {/* Appointment Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                          {apt.student_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-800">{apt.title}</h3>
                          <p className="text-sm text-slate-600">with {apt.student_name}</p>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {format(parseISO(apt.date), 'EEEE, MMMM d, yyyy')}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {format(parseISO(apt.date), 'h:mm a')} ({apt.duration_minutes} min)
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[apt.status]}`}>
                          <StatusIcon className="w-3.5 h-3.5" />
                          {apt.status.charAt(0).toUpperCase() + apt.status.slice(1)}
                        </span>
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                          {apt.appointment_type}
                        </span>
                      </div>
                      
                      {apt.notes && (
                        <div className="mt-3 p-3 bg-slate-50 rounded-lg">
                          <p className="text-sm text-slate-600">
                            <span className="font-medium">Notes:</span> {apt.notes}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-wrap gap-2">
                      {apt.status === 'pending' && !isPast && (
                        <>
                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'confirmed')}
                            disabled={isUpdating}
                            className="flex items-center gap-1 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium disabled:opacity-50"
                          >
                            <CheckCircle className="w-4 h-4" />
                            Confirm
                          </button>
                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'cancelled')}
                            disabled={isUpdating}
                            className="flex items-center gap-1 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium disabled:opacity-50"
                          >
                            <XCircle className="w-4 h-4" />
                            Decline
                          </button>
                        </>
                      )}
                      
                      {apt.status === 'confirmed' && (
                        <button
                          onClick={() => handleStatusUpdate(apt.id, 'completed')}
                          disabled={isUpdating}
                          className="flex items-center gap-1 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium disabled:opacity-50"
                        >
                          <CheckCircle className="w-4 h-4" />
                          Mark Complete
                        </button>
                      )}
                      
                      {apt.status !== 'cancelled' && (
                        <button
                          onClick={() => openNotesModal(apt)}
                          className="flex items-center gap-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                        >
                          <FileText className="w-4 h-4" />
                          {apt.notes ? 'Edit Notes' : 'Add Notes'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Notes Modal */}
      {showNotesModal && selectedAppointment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="text-xl font-semibold text-slate-800">
                Session Notes
              </h2>
              <button
                onClick={() => {
                  setShowNotesModal(false);
                  setSelectedAppointment(null);
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            
            <div className="p-6">
              <div className="mb-4 p-4 bg-slate-50 rounded-xl">
                <p className="font-medium text-slate-800">{selectedAppointment.title}</p>
                <p className="text-sm text-slate-600">
                  {selectedAppointment.student_name} • {format(parseISO(selectedAppointment.date), 'MMM d, yyyy')}
                </p>
              </div>
              
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Notes (private to counsellors)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={6}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all resize-none"
                placeholder="Add session notes, observations, or follow-up items..."
              />
            </div>
            
            <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-100">
              <button
                onClick={() => {
                  setShowNotesModal(false);
                  setSelectedAppointment(null);
                }}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddNotes}
                disabled={isUpdating}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {isUpdating ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
