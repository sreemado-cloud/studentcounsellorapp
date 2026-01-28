import { useEffect, useState } from 'react';
import { messagesApi, usersApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import type { Message, Conversation, User } from '../types';
import { format } from 'date-fns';
import {
  MessageSquare,
  Send,
  Search,
  Plus,
  X,
  ChevronLeft,
} from 'lucide-react';

export default function Messages() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [counsellors, setCounsellors] = useState<User[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [selectedRecipient, setSelectedRecipient] = useState('');
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const isStudent = user?.role === 'student';
  const assignedCounsellorId = user?.assigned_counsellor_id ?? null;

  const fetchData = async () => {
    try {
      const [conversationsData, messagesData] = await Promise.all([
        messagesApi.getConversations(),
        messagesApi.getAll(),
      ]);
      setConversations(conversationsData);
      setMessages(messagesData);
      if (!isStudent) {
        const counsellorsData = await usersApi.getCounsellors();
        setCounsellors(counsellorsData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getConversationMessages = (participantId: string) => {
    return messages.filter(
      (msg) =>
        msg.sender_id === participantId || msg.recipient_id === participantId
    ).sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const recipientId = isStudent ? assignedCounsellorId : (selectedConversation || selectedRecipient);
    if (!recipientId) return;

    setIsSending(true);
    try {
      await messagesApi.send({
        recipient_id: recipientId,
        content: newMessage,
      });
      setNewMessage('');
      setShowNewMessage(false);
      setSelectedRecipient('');
      fetchData();
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const selectedParticipant = conversations.find(
    (c) => c.participant_id === selectedConversation
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Messages</h1>
          <p className="text-slate-500">
            {isStudent ? 'Chat with your counsellor' : 'Chat with your counsellors'}
          </p>
        </div>
        {!isStudent && (
          <button
            onClick={() => setShowNewMessage(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all"
          >
            <Plus className="w-5 h-5" />
            New Message
          </button>
        )}
        {isStudent && assignedCounsellorId && (
          <button
            onClick={() => {
              setSelectedRecipient(assignedCounsellorId);
              setShowNewMessage(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all"
          >
            <Plus className="w-5 h-5" />
            New Message
          </button>
        )}
      </div>

      <div className="flex-1 bg-white rounded-2xl border border-slate-100 overflow-hidden flex">
        {/* Conversations List */}
        <div
          className={`w-full md:w-80 border-r border-slate-100 flex flex-col ${
            selectedConversation ? 'hidden md:flex' : 'flex'
          }`}
        >
          <div className="p-4 border-b border-slate-100">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <div className="p-8 text-center">
                <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">
                  {isStudent && !assignedCounsellorId
                    ? "You don't have an assigned counsellor. Contact an admin."
                    : 'No conversations yet'}
                </p>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.participant_id}
                  onClick={() => setSelectedConversation(conv.participant_id)}
                  className={`w-full p-4 flex items-center gap-3 hover:bg-slate-50 transition-colors border-b border-slate-50 ${
                    selectedConversation === conv.participant_id ? 'bg-indigo-50' : ''
                  }`}
                >
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                    {conv.participant_name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-slate-800 truncate">
                        {conv.participant_name}
                      </p>
                      {conv.unread_count > 0 && (
                        <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 truncate">{conv.last_message}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div
          className={`flex-1 flex flex-col ${
            selectedConversation ? 'flex' : 'hidden md:flex'
          }`}
        >
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-slate-100 flex items-center gap-3">
                <button
                  onClick={() => setSelectedConversation(null)}
                  className="md:hidden p-2 hover:bg-slate-100 rounded-lg"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                  {selectedParticipant?.participant_name.charAt(0)}
                </div>
                <div>
                  <p className="font-medium text-slate-800">
                    {selectedParticipant?.participant_name}
                  </p>
                  <p className="text-sm text-slate-500 capitalize">
                    {selectedParticipant?.participant_role}
                  </p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {getConversationMessages(selectedConversation).map((msg) => {
                  const isOwn = msg.sender_id === user?.id;
                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                          isOwn
                            ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                            : 'bg-slate-100 text-slate-800'
                        }`}
                      >
                        <p>{msg.content}</p>
                        <p
                          className={`text-xs mt-1 ${
                            isOwn ? 'text-indigo-200' : 'text-slate-500'
                          }`}
                        >
                          {format(new Date(msg.created_at), 'h:mm a')}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Input */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    disabled={isSending || !newMessage.trim()}
                    className="px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all disabled:opacity-50"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-800 mb-2">
                  Select a conversation
                </h3>
                <p className="text-slate-500">
                  Choose a conversation from the list or start a new one
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* New Message Modal */}
      {showNewMessage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl w-full max-w-lg">
            <div className="p-6 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-800">New Message</h2>
                <button
                  type="button"
                  onClick={() => {
                    setShowNewMessage(false);
                    setSelectedRecipient('');
                    setNewMessage('');
                  }}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <form onSubmit={handleSendMessage} className="p-6 space-y-5">
              {isStudent ? (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    To
                  </label>
                  <div className="px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700">
                    {user?.assigned_counsellor_name ?? 'Your assigned counsellor'}
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    To
                  </label>
                  <select
                    value={selectedRecipient}
                    onChange={(e) => setSelectedRecipient(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  >
                    <option value="">Select a counsellor</option>
                    {counsellors.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.full_name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Message
                </label>
                <textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                  placeholder="Type your message..."
                  required
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowNewMessage(false);
                    setSelectedRecipient('');
                    setNewMessage('');
                  }}
                  className="flex-1 px-4 py-3 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={
                    isSending ||
                    (!isStudent && !selectedRecipient) ||
                    (isStudent && !assignedCounsellorId) ||
                    !newMessage.trim()
                  }
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all disabled:opacity-50"
                >
                  {isSending ? 'Sending...' : 'Send Message'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
