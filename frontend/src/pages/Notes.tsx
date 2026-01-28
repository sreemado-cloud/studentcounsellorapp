import { useEffect, useState } from 'react';
import { notesApi } from '../services/api';
import type { Note, NoteCategory } from '../types';
import { format } from 'date-fns';
import {
  FileText,
  Plus,
  Search,
  X,
  Trash2,
  Edit3,
  Tag,
  Folder,
} from 'lucide-react';

const categories: { value: NoteCategory; label: string; color: string }[] = [
  { value: 'general', label: 'General', color: 'bg-slate-500' },
  { value: 'academic', label: 'Academic', color: 'bg-blue-500' },
  { value: 'career', label: 'Career', color: 'bg-purple-500' },
  { value: 'personal', label: 'Personal', color: 'bg-pink-500' },
  { value: 'goals', label: 'Goals', color: 'bg-green-500' },
  { value: 'resources', label: 'Resources', color: 'bg-amber-500' },
];

export default function Notes() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Form state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<NoteCategory>('general');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    try {
      const data = await notesApi.getAll();
      setNotes(data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const noteData = {
        title,
        content,
        category,
        tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
        is_private: true,
      };

      if (editingNote) {
        await notesApi.update(editingNote.id, noteData);
      } else {
        await notesApi.create(noteData);
      }

      setShowModal(false);
      resetForm();
      fetchNotes();
    } catch (error) {
      console.error('Error saving note:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (note: Note) => {
    setEditingNote(note);
    setTitle(note.title);
    setContent(note.content);
    setCategory(note.category);
    setTags(note.tags.join(', '));
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      try {
        await notesApi.delete(id);
        fetchNotes();
      } catch (error) {
        console.error('Error deleting note:', error);
      }
    }
  };

  const resetForm = () => {
    setTitle('');
    setContent('');
    setCategory('general');
    setTags('');
    setEditingNote(null);
  };

  const getCategoryInfo = (cat: string) => {
    return categories.find((c) => c.value === cat) || categories[0];
  };

  const filteredNotes = notes.filter((note) => {
    const matchesCategory = filterCategory === 'all' || note.category === filterCategory;
    const matchesSearch =
      !searchQuery ||
      note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
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
          <h1 className="text-2xl font-bold text-slate-800">My Notes</h1>
          <p className="text-slate-500">Keep track of your thoughts and goals</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all"
        >
          <Plus className="w-5 h-5" />
          New Note
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search notes..."
            className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
          <button
            onClick={() => setFilterCategory('all')}
            className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
              filterCategory === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setFilterCategory(cat.value)}
              className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
                filterCategory === cat.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Notes Grid */}
      {filteredNotes.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
          <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">No notes found</h3>
          <p className="text-slate-500 mb-4">
            {notes.length === 0
              ? 'Start by creating your first note'
              : 'Try adjusting your search or filters'}
          </p>
          <button
            onClick={() => {
              resetForm();
              setShowModal(true);
            }}
            className="inline-flex items-center gap-2 text-indigo-600 font-medium"
          >
            <Plus className="w-4 h-4" />
            Create a note
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotes.map((note) => {
            const catInfo = getCategoryInfo(note.category);
            return (
              <div
                key={note.id}
                className="bg-white rounded-2xl border border-slate-100 overflow-hidden hover:shadow-lg transition-shadow group"
              >
                <div className={`h-2 ${catInfo.color}`} />
                <div className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold text-slate-800 text-lg line-clamp-1">
                      {note.title}
                    </h3>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleEdit(note)}
                        className="p-2 hover:bg-slate-100 rounded-lg text-slate-500"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(note.id)}
                        className="p-2 hover:bg-red-50 rounded-lg text-red-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <p className="text-slate-600 text-sm line-clamp-3 mb-4">{note.content}</p>

                  <div className="flex items-center gap-2 mb-3">
                    <span className="flex items-center gap-1 text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-md">
                      <Folder className="w-3 h-3" />
                      {catInfo.label}
                    </span>
                  </div>

                  {note.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {note.tags.slice(0, 3).map((tag, idx) => (
                        <span
                          key={idx}
                          className="flex items-center gap-1 text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md"
                        >
                          <Tag className="w-3 h-3" />
                          {tag}
                        </span>
                      ))}
                      {note.tags.length > 3 && (
                        <span className="text-xs text-slate-500">
                          +{note.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-slate-400">
                    {format(new Date(note.created_at), 'MMM d, yyyy')}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-800">
                  {editingNote ? 'Edit Note' : 'New Note'}
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Note title"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as NoteCategory)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {categories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Content
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                  placeholder="Write your note..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="e.g., important, exam, project"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-3 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/30 hover:shadow-xl transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : editingNote ? 'Update Note' : 'Create Note'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
