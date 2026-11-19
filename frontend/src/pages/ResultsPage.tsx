import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Download,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowLeft,
  Loader2,
  Award,
  Target,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { api } from '../services/api';
import type { SessionData } from '../types';

export const ResultsPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId]);

  const loadSession = async (sid: string) => {
    setLoading(true);
    try {
      const data = await api.getSession(sid);
      setSession(data);
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
        <span className="text-sm font-semibold">Compiling interview results and analytics...</span>
      </div>
    );
  }

  if (!session || !sessionId) {
    return (
      <div className="py-16 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Session Not Found</h2>
        <Link to="/dashboard" className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const avgScore =
    session.answers.length > 0
      ? (session.answers.reduce((acc, a) => acc + a.feedback.score, 0) / session.answers.length).toFixed(1)
      : '0.0';

  const chartData = session.answers.map((a, i) => ({
    name: `Q${i + 1}`,
    topic: a.topic,
    score: a.feedback.score,
  }));

  const pdfDownloadUrl = api.getReportUrl(sessionId);

  return (
    <div className="max-w-5xl mx-auto space-y-6 sm:space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-navy-700">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 mb-2 cursor-pointer transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Interview Evaluation Report
          </h1>
          <p className="text-sm text-slate-600 dark:text-[#CBD5E1] mt-1">
            Session ID: <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{sessionId}</span> &bull; Completed {session.answers.length} of {session.config.num_questions} questions
          </p>
        </div>

        <a
          href={pdfDownloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-600/30 transition-all self-start sm:self-auto cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Download PDF Report</span>
        </a>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        <div className="rounded-2xl p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Overall Rating</span>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-slate-900 dark:text-white">{avgScore}</span>
            <span className="text-sm text-slate-400 font-bold">/ 10</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Average score across all rounds</p>
        </div>

        <div className="rounded-2xl p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Questions Completed</span>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {session.answers.length} <span className="text-sm text-slate-400 font-normal">/ {session.config.num_questions}</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Interview format: {session.config.interview_type}</p>
        </div>

        <div className="rounded-2xl p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Preparation Verdict</span>
          <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
            <Award className="w-5 h-5" />
            <span>{Number(avgScore) >= 8 ? 'Interview Ready' : Number(avgScore) >= 6 ? 'Solid Foundation' : 'Requires Focus'}</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Based on objective rubric criteria</p>
        </div>
      </div>

      {/* Progression Bar Chart */}
      {chartData.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span>Round-by-Round Score Progression</span>
          </h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis domain={[0, 10]} stroke="#94a3b8" fontSize={12} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-3 rounded-xl bg-slate-900 dark:bg-navy-950 text-white text-xs shadow-lg space-y-1 border border-slate-700">
                          <p className="font-bold">{data.topic}</p>
                          <p className="text-indigo-300">Score: {data.score} / 10</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.score >= 8 ? '#10b981' : entry.score <= 4 ? '#f43f5e' : '#6366f1'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Skill Gap Analysis */}
      {session.skill_gap && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Demonstrated & Matched Competencies ({session.skill_gap.matched.length})</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {session.skill_gap.matched.map((skill, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-amber-800 dark:text-amber-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              <span>Target Growth & Practice Areas ({session.skill_gap.missing.length})</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {session.skill_gap.missing.map((skill, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700/60"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Question Review Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Question Review & Model Answers</h2>

        {session.answers.map((a, i) => (
          <div
            key={a.attempt_id}
            className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-navy-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-indigo-50 dark:bg-navy-800 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60">
                  Round {i + 1}: {a.topic}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 capitalize font-medium">({a.difficulty})</span>
              </div>
              <span className="text-lg font-extrabold text-slate-900 dark:text-white">
                {a.feedback.score} <span className="text-xs text-slate-400">/ 10</span>
              </span>
            </div>

            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">❓ {a.question_text}</h3>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-navy-750 text-xs space-y-1">
              <span className="font-bold text-slate-500 dark:text-slate-400 block uppercase text-[10px]">Candidate Submitted Answer:</span>
              <p className="text-slate-800 dark:text-slate-200 font-mono leading-relaxed">{a.answer_text}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800/60 space-y-1.5">
                <span className="font-bold text-emerald-900 dark:text-emerald-300 block">Strengths:</span>
                <ul className="list-disc list-inside text-slate-800 dark:text-slate-200 space-y-1">
                  {a.feedback.strengths.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800/60 space-y-1.5">
                <span className="font-bold text-amber-900 dark:text-amber-300 block">Identified Gaps:</span>
                <ul className="list-disc list-inside text-slate-800 dark:text-slate-200 space-y-1">
                  {a.feedback.gaps.map((g, idx) => (
                    <li key={idx}>{g}</li>
                  ))}
                </ul>
              </div>
            </div>

            {a.feedback.model_answer && (
              <details className="text-xs pt-1">
                <summary className="font-bold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer list-none flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Reveal 10/10 Benchmark Model Answer</span>
                </summary>
                <p className="mt-2 text-xs font-mono text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-navy-950 p-3.5 rounded-xl border border-slate-200 dark:border-navy-750 whitespace-pre-wrap leading-relaxed">
                  {a.feedback.model_answer}
                </p>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
