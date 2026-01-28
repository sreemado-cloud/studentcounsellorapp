import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { institutionsApi, messagesApi } from '../services/api';
import type { User } from '../types';
import {
  Users,
  Search,
  MessageSquare,
  Calendar,
  GraduationCap,
  BookOpen,
  X,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';

export default function Students() {
  const [students, setStudents] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<User | null>(null);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [messageContent, setMessageContent] = useState('');
  const [messageSubject, setMessageSubject] = useState('');
  const [isSending, setIsSending] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const data = await institutionsApi.getUsers('student');
      setStudents(data);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedStudent || !messageContent.trim()) return;
    
    setIsSending(true);
    try {
      await messagesApi.send({
        recipient_id: selectedStudent.id,
        content: messageContent,
        subject: messageSubject || undefined,
      });
      setShowMessageModal(false);
      setSelectedStudent(null);
      setMessageContent('');
      setMessageSubject('');
      // Navigate to messages page
      navigate('/messages');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const openMessageModal = (student: User) => {
    setSelectedStudent(student);
    setShowMessageModal(true);
  };

  // Filter students by search query
  const filteredStudents = students.filter((student) => {
    const query = searchQuery.toLowerCase();
    return (
      student.full_name.toLowerCase().includes(query) ||
      student.email.toLowerCase().includes(query) ||
      student.major?.toLowerCase().includes(query) ||
      student.grade?.toLowerCase().includes(query)
    );
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
          <h1 className="text-3xl font-bold text-slate-800">Students</h1>
          <p className="text-slate-600 mt-1">
            {students.length} student{students.length !== 1 ? 's' : ''} in your institution
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, email, major, or grade..."
            className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
          />
        </div>
      </div>

      {/* Students Grid */}
      {filteredStudents.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-12 text-center">
          <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">
            {searchQuery ? 'No students match your search' : 'No students found'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStudents.map((student) => (
            <div
              key={student.id}
              className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold text-xl flex-shrink-0">
                  {student.full_name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-800 truncate">
                    {student.full_name}
                  </h3>
                  <p className="text-sm text-slate-500 truncate">{student.email}</p>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                {student.grade && (
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <GraduationCap className="w-4 h-4 text-slate-400" />
                    <span>{student.grade}</span>
                  </div>
                )}
                {student.major && (
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <BookOpen className="w-4 h-4 text-slate-400" />
                    <span>{student.major}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span>Joined {format(parseISO(student.created_at), 'MMM yyyy')}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 flex gap-2">
                <button
                  onClick={() => openMessageModal(student)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors text-sm font-medium"
                >
                  <MessageSquare className="w-4 h-4" />
                  Message
                </button>
                <button
                  onClick={() => navigate('/appointments')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                >
                  <Calendar className="w-4 h-4" />
                  Sessions
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Message Modal */}
      {showMessageModal && selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Send Message</h2>
                <p className="text-sm text-slate-500">to {selectedStudent.full_name}</p>
              </div>
              <button
                onClick={() => {
                  setShowMessageModal(false);
                  setSelectedStudent(null);
                  setMessageContent('');
                  setMessageSubject('');
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Subject (optional)
                </label>
                <input
                  type="text"
                  value={messageSubject}
                  onChange={(e) => setMessageSubject(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="Message subject..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Message
                </label>
                <textarea
                  value={messageContent}
                  onChange={(e) => setMessageContent(e.target.value)}
                  rows={5}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all resize-none"
                  placeholder="Type your message..."
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-100">
              <button
                onClick={() => {
                  setShowMessageModal(false);
                  setSelectedStudent(null);
                  setMessageContent('');
                  setMessageSubject('');
                }}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSendMessage}
                disabled={!messageContent.trim() || isSending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSending ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
