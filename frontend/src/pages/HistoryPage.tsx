import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  ArrowRight,
  Loader2,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import type { SessionSummary } from '../types';

export const HistoryPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'in_progress'>('all');

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await api.listSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load session history:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredSessions = sessions.filter((s) => {
    const matchesSearch =
      s.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.interview_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.difficulty.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === 'all' ? true : s.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6 sm:space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-navy-700">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Interview History
          </h1>
          <p className="text-sm text-slate-600 dark:text-[#CBD5E1] mt-1">
            Review past mock interview sessions, questions asked, and objective rubric evaluations.
          </p>
        </div>
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-600/30 transition-all self-start sm:self-auto cursor-pointer"
        >
          <span>Start New Interview</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search sessions by ID or type..."
            className="w-full pl-9 pr-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
          />
        </div>

        <div className="flex items-center gap-1.5 self-end sm:self-auto">
          {(['all', 'completed', 'in_progress'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-colors cursor-pointer ${
                statusFilter === st
                  ? 'bg-indigo-50 dark:bg-navy-800 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/80 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center space-y-3 text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
          <span className="text-sm font-semibold">Retrieving saved interviews...</span>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-12 text-center space-y-3 shadow-xs">
          <HistoryIcon className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">No matching sessions found</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            {searchTerm ? 'Try a different search query.' : 'Initiate a mock interview to start building your interview history.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredSessions.map((s) => (
            <div
              key={s.id}
              className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {s.id.slice(0, 12)}...
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                      s.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60'
                        : 'bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-700/60'
                    }`}
                  >
                    {s.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
                  <span>Type: <strong className="text-slate-900 dark:text-white capitalize">{s.interview_type}</strong></span>
                  <span>&bull;</span>
                  <span>Difficulty: <strong className="text-violet-600 dark:text-violet-400 capitalize">{s.difficulty}</strong></span>
                  <span>&bull;</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(s.created_at).toLocaleDateString()}</span>
                  </span>
                  <span>&bull;</span>
                  <span>Completed: <strong className="text-slate-900 dark:text-white">{s.completed_questions} / {s.total_questions}</strong> Qs</span>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-auto">
                {s.average_score !== undefined && s.average_score !== null && (
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-bold">Average</span>
                    <span className="text-base font-extrabold text-slate-900 dark:text-white">
                      {s.average_score} <span className="text-xs text-slate-400 font-normal">/ 10</span>
                    </span>
                  </div>
                )}

                {s.status === 'completed' ? (
                  <Link
                    to={`/results/${s.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-navy-800 hover:bg-indigo-100 dark:hover:bg-navy-700 transition-colors border border-indigo-200 dark:border-navy-700"
                  >
                    <span>View Results</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                ) : (
                  <Link
                    to={`/interview/${s.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-xs"
                  >
                    <span>Resume</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
