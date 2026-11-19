import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PlusCircle,
  History,
  TrendingUp,
  Award,
  CheckCircle2,
  Clock,
  ArrowRight,
  Loader2,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import type { SessionSummary } from '../types';

export const DashboardPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listSessions();
      setSessions(data);
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
      setError('Could not connect to FastAPI backend. Ensure backend is running at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  const completedSessions = sessions.filter((s) => s.status === 'completed');
  const scoresWithValues = sessions
    .map((s) => s.average_score)
    .filter((s): s is number => typeof s === 'number' && !isNaN(s));
  const avgOverallScore =
    scoresWithValues.length > 0
      ? (scoresWithValues.reduce((a, b) => a + b, 0) / scoresWithValues.length).toFixed(1)
      : null;

  return (
    <div className="space-y-8">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-navy-700">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Interview Preparation Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Track your mock interview progress, target skill gaps, and review past performance.
          </p>
        </div>
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 shadow-sm shadow-primary-600/25 transition-all self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Mock Interview</span>
        </Link>
      </div>

      {/* Error alert */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl p-5 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Interviews</span>
            <FileText className="w-4 h-4 text-primary-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white">{sessions.length}</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Total sessions initiated</p>
        </div>

        <div className="rounded-2xl p-5 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white">{completedSessions.length}</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Finished mock rounds</p>
        </div>

        <div className="rounded-2xl p-5 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Average Score</span>
            <Award className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white">
            {avgOverallScore ? `${avgOverallScore} / 10` : '—'}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Across graded answers</p>
        </div>

        <div className="rounded-2xl p-5 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Target Domain</span>
            <TrendingUp className="w-4 h-4 text-violet-500" />
          </div>
          <div className="text-xl font-bold text-slate-900 dark:text-white">AI Engineering</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">RAG & Agentic Systems</p>
        </div>
      </div>

      {/* Recent Sessions Table */}
      <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 dark:border-navy-700 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-500" />
            <span>Recent Interview Sessions</span>
          </h2>
          <Link
            to="/history"
            className="text-xs font-semibold text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            <span className="text-sm">Loading interview history...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-navy-800 text-slate-400 flex items-center justify-center mx-auto">
              <History className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">No interviews recorded yet</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
              Upload your resume and job description to initiate your first grounded technical mock interview.
            </p>
            <div className="pt-2">
              <Link
                to="/documents"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 shadow-sm transition-all"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Start First Interview</span>
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-navy-800/50 text-slate-500 dark:text-slate-400 text-xs uppercase font-semibold border-b border-slate-200 dark:border-navy-700">
                <tr>
                  <th className="px-5 py-3.5">Session ID</th>
                  <th className="px-5 py-3.5">Date</th>
                  <th className="px-5 py-3.5">Type & Difficulty</th>
                  <th className="px-5 py-3.5">Questions</th>
                  <th className="px-5 py-3.5">Average Score</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-navy-700">
                {sessions.slice(0, 5).map((session) => (
                  <tr key={session.id} className="hover:bg-slate-50/50 dark:hover:bg-navy-800/40 transition-colors">
                    <td className="px-5 py-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                      {session.id.slice(0, 8)}...
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-500 dark:text-slate-400">
                      {new Date(session.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-slate-900 dark:text-white capitalize">
                          {session.interview_type}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-750 text-slate-600 dark:text-slate-300 capitalize">
                          {session.difficulty}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-600 dark:text-slate-300">
                      {session.completed_questions} / {session.total_questions}
                    </td>
                    <td className="px-5 py-4">
                      {session.average_score !== undefined && session.average_score !== null ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-primary-50 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300">
                          {session.average_score} / 10
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">Incomplete</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium capitalize ${
                          session.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400'
                            : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400'
                        }`}
                      >
                        {session.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      {session.status === 'completed' ? (
                        <Link
                          to={`/results/${session.id}`}
                          className="text-xs font-semibold text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          View Results
                        </Link>
                      ) : (
                        <Link
                          to={`/interview/${session.id}`}
                          className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                        >
                          Resume &rarr;
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
