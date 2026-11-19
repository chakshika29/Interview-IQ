import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  ArrowLeft,
  Loader2,
  Sparkles,
  AlertCircle,
  Mic,
  MessageSquare,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  AnswerMethod,
  InterviewConfig,
  InterviewDifficulty,
  InterviewType,
} from '../types';

interface ConfigurePageProps {
  onSessionCreated?: (sessionId: string) => void;
}

export const ConfigurePage: React.FC<ConfigurePageProps> = ({ onSessionCreated }) => {
  const navigate = useNavigate();

  const resumeText = sessionStorage.getItem('interviewiq_resume_text') || '';
  const jdText = sessionStorage.getItem('interviewiq_jd_text') || '';

  const [interviewType, setInterviewType] = useState<InterviewType>('technical');
  const [difficulty, setDifficulty] = useState<InterviewDifficulty>('adaptive');
  const [numQuestions, setNumQuestions] = useState<number>(5);
  const [answerMethod, setAnswerMethod] = useState<AnswerMethod>('voice_text');
  const [timeLimit] = useState<number>(120);
  const [enableFollowup] = useState<boolean>(true);
  const [enableDetailedFeedback] = useState<boolean>(true);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleStartInterview = async () => {
    if (!resumeText || !jdText) {
      setErrorMsg('Documents not found in session memory. Please return to Document Setup and upload your resume and job description.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    const config: InterviewConfig = {
      interview_type: interviewType,
      difficulty: difficulty,
      num_questions: numQuestions,
      answer_method: answerMethod,
      time_limit_seconds: timeLimit,
      enable_followup: enableFollowup,
      enable_video: false,
      enable_detailed_feedback: enableDetailedFeedback,
    };

    try {
      const session = await api.createSession({
        resume_text: resumeText,
        job_text: jdText,
        config: config,
      });

      if (onSessionCreated) {
        onSessionCreated(session.id);
      }
      navigate(`/interview/${session.id}`);
    } catch (err: any) {
      console.error('Failed to create session:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to initialize interview session.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-navy-700">
        <div>
          <button
            type="button"
            onClick={() => navigate('/documents')}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 mb-2 cursor-pointer transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Documents</span>
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Interview Configuration
          </h1>
          <p className="text-sm text-slate-600 dark:text-[#CBD5E1] mt-1">
            Customize the interview focus, adaptive difficulty level, and answer submission mode.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-start gap-2.5 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Interview Type Selection */}
          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
            <label className="block text-sm font-bold text-slate-900 dark:text-white">Interview Type</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                { id: 'technical', label: 'Technical', desc: 'Architecture & code' },
                { id: 'behavioral', label: 'Behavioral', desc: 'STAR methodology' },
                { id: 'hr', label: 'HR / Fit', desc: 'Culture & values' },
                { id: 'mixed', label: 'Mixed', desc: 'Balanced simulation' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setInterviewType(t.id as InterviewType)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    interviewType === t.id
                      ? 'border-indigo-600 bg-indigo-50/80 dark:bg-navy-800 text-indigo-700 dark:text-indigo-300 ring-2 ring-indigo-500/25 font-bold shadow-xs'
                      : 'border-slate-200 dark:border-navy-700 hover:border-slate-300 dark:hover:border-navy-600'
                  }`}
                >
                  <span className="block text-xs font-bold text-slate-900 dark:text-white">{t.label}</span>
                  <span className="block text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{t.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty Progression */}
          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-900 dark:text-white">Progression Difficulty</label>
              {difficulty === 'adaptive' && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-violet-600 dark:text-violet-400">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Dynamic AI Recalibration</span>
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                { id: 'adaptive', label: 'Adaptive', tag: 'Recommended' },
                { id: 'beginner', label: 'Beginner', tag: 'Foundational' },
                { id: 'intermediate', label: 'Intermediate', tag: 'Standard' },
                { id: 'advanced', label: 'Advanced', tag: 'Principal Level' },
              ].map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDifficulty(d.id as InterviewDifficulty)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    difficulty === d.id
                      ? 'border-violet-600 bg-violet-50/80 dark:bg-navy-800 text-violet-700 dark:text-violet-300 ring-2 ring-violet-500/25 font-bold shadow-xs'
                      : 'border-slate-200 dark:border-navy-700 hover:border-slate-300 dark:hover:border-navy-600'
                  }`}
                >
                  <span className="block text-xs font-bold text-slate-900 dark:text-white">{d.label}</span>
                  <span className="block text-[10px] text-violet-600 dark:text-violet-400 font-semibold mt-0.5">{d.tag}</span>
                </button>
              ))}
            </div>

            {difficulty === 'adaptive' && (
              <p className="text-[11px] text-slate-600 dark:text-[#CBD5E1] leading-relaxed bg-slate-50 dark:bg-navy-900 p-3 rounded-xl border border-slate-200 dark:border-navy-750">
                💡 <b>Adaptive Loop</b>: Scores &ge; 8 promote to harder questions testing production edge cases. Scores &le; 4 trigger a simpler follow-up on the same weak topic to test foundational knowledge.
              </p>
            )}
          </div>

          {/* Question Count & Answer Mode */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
              <label className="block text-sm font-bold text-slate-900 dark:text-white">Question Count</label>
              <div className="grid grid-cols-4 gap-2">
                {[5, 10, 15, 20].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setNumQuestions(num)}
                    className={`py-2 text-center rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                      numQuestions === num
                        ? 'border-indigo-600 bg-indigo-600 text-white shadow-xs'
                        : 'border-slate-200 dark:border-navy-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-navy-800'
                    }`}
                  >
                    {num} Qs
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
              <label className="block text-sm font-bold text-slate-900 dark:text-white">Answer Method</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'voice_text', label: 'Voice+Text', icon: Mic },
                  { id: 'voice', label: 'Voice Only', icon: Mic },
                  { id: 'text', label: 'Text Only', icon: MessageSquare },
                ].map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setAnswerMethod(m.id as AnswerMethod)}
                    className={`p-2 text-center rounded-xl border transition-all cursor-pointer ${
                      answerMethod === m.id
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-navy-800 text-indigo-700 dark:text-indigo-300 font-bold'
                        : 'border-slate-200 dark:border-navy-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-navy-800'
                    }`}
                  >
                    <span className="block text-[11px] font-bold">{m.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Summary Card */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4 sticky top-24">
            <h3 className="font-extrabold text-slate-900 dark:text-white uppercase tracking-wider text-xs border-b border-slate-200 dark:border-navy-700 pb-3">
              Session Summary
            </h3>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Target Role:</span>
                <span className="font-bold text-slate-900 dark:text-white">AI Platform Engineer</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Interview Type:</span>
                <span className="font-bold text-slate-900 dark:text-white capitalize">{interviewType}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Difficulty:</span>
                <span className="font-bold text-violet-600 dark:text-violet-400 capitalize">{difficulty}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Question Quota:</span>
                <span className="font-bold text-slate-900 dark:text-white">{numQuestions} Questions</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Time per Question:</span>
                <span className="font-bold text-slate-900 dark:text-white">{timeLimit} seconds</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-navy-800">
                <span className="text-slate-500 dark:text-slate-400">Speech-to-Text:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">Gemini Multimodal STT</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleStartInterview}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md shadow-indigo-600/30 active:scale-95 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Building RAG Vector Index...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Begin Mock Interview</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
