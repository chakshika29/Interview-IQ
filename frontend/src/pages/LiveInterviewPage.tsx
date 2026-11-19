import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Sparkles,
  ArrowRight,
  Loader2,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  Send,
} from 'lucide-react';
import { api } from '../services/api';
import { AudioRecorder } from '../components/AudioRecorder';
import type {
  AnswerAttempt,
  DetailedFeedback,
  QuestionDetail,
  SessionData,
} from '../types';

export const LiveInterviewPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<SessionData | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionDetail | null>(null);
  const [answerText, setAnswerText] = useState<string>('');
  const [recordedAudioFile, setRecordedAudioFile] = useState<string | null>(null);
  const [originalTranscript, setOriginalTranscript] = useState<string | null>(null);
  const [transcriptEdited, setTranscriptEdited] = useState(false);

  const [feedback, setFeedback] = useState<DetailedFeedback | null>(null);
  const [loadingSession, setLoadingSession] = useState(true);
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [generatingNextQ, setGeneratingNextQ] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionData(sessionId);
    }
  }, [sessionId]);

  const loadSessionData = async (sid: string) => {
    setLoadingSession(true);
    setErrorMsg(null);
    try {
      const data = await api.getSession(sid);
      setSession(data);

      if (data.questions.length === 0) {
        await fetchNextQuestion(sid);
      } else {
        const lastQ = data.questions[data.questions.length - 1];
        setCurrentQuestion(lastQ);
        const lastAnswer = data.answers.find((a) => a.question_id === lastQ.id);
        if (lastAnswer) {
          setFeedback(lastAnswer.feedback);
          setAnswerText(lastAnswer.answer_text);
        }
      }
    } catch (err: any) {
      console.error('Failed to load session:', err);
      setErrorMsg(err.response?.data?.detail || 'Unable to retrieve interview session.');
    } finally {
      setLoadingSession(false);
    }
  };

  const fetchNextQuestion = async (sid: string) => {
    setGeneratingNextQ(true);
    setErrorMsg(null);
    try {
      const q = await api.getNextQuestion(sid);
      setCurrentQuestion(q);
      setFeedback(null);
      setAnswerText('');
      setRecordedAudioFile(null);
      setOriginalTranscript(null);
      setTranscriptEdited(false);
    } catch (err: any) {
      console.error('Error fetching question:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to generate interview question.');
    } finally {
      setGeneratingNextQ(false);
    }
  };

  const handleTranscriptionComplete = (transcript: string, audioFilename: string) => {
    setOriginalTranscript(transcript);
    setRecordedAudioFile(audioFilename);
    setAnswerText(transcript);
    setTranscriptEdited(false);
  };

  const handleAnswerTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAnswerText(e.target.value);
    if (originalTranscript && e.target.value !== originalTranscript) {
      setTranscriptEdited(true);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!sessionId || !currentQuestion || !answerText.trim()) {
      setErrorMsg('Please record or type an answer before scoring.');
      return;
    }

    setSubmittingAnswer(true);
    setErrorMsg(null);

    try {
      const attempt: AnswerAttempt = await api.submitAnswer(sessionId, {
        question_id: currentQuestion.id,
        answer_text: answerText.trim(),
        audio_filename: recordedAudioFile,
        original_transcript: originalTranscript,
        transcript_edited: transcriptEdited,
      });

      setFeedback(attempt.feedback);

      const updated = await api.getSession(sessionId);
      setSession(updated);
    } catch (err: any) {
      console.error('Scoring error:', err);
      setErrorMsg(err.response?.data?.detail || 'Answer evaluation failed. Please try again.');
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleNextOrFinish = async () => {
    if (!sessionId || !session) return;

    if (session.answers.length >= session.config.num_questions) {
      await api.completeInterview(sessionId);
      navigate(`/results/${sessionId}`);
    } else {
      await fetchNextQuestion(sessionId);
    }
  };

  if (loadingSession) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
        <span className="text-sm font-semibold">Initializing mock interview session...</span>
      </div>
    );
  }

  if (!session || !sessionId) {
    return (
      <div className="py-16 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Session Not Found</h2>
        <button
          onClick={() => navigate('/documents')}
          className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Return to Document Ingestion
        </button>
      </div>
    );
  }

  const totalQNum = session.config.num_questions;
  const isLastQuestion = session.answers.length >= session.config.num_questions;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Top Session Progress Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider bg-indigo-50 dark:bg-navy-800 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60">
            Round {session.answers.length + 1} of {totalQNum}
          </span>
          <span className="text-xs text-slate-600 dark:text-slate-300 capitalize hidden sm:inline font-semibold">
            {session.config.interview_type} &bull; {session.config.difficulty}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
          <span>Session:</span>
          <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{sessionId.slice(0, 8)}</span>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-start gap-2.5 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Active Question Card */}
      {currentQuestion && (
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-navy-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-violet-50 dark:bg-violet-950/80 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800/60">
                {currentQuestion.topic}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded text-[11px] font-bold uppercase ${
                  currentQuestion.difficulty === 'easy'
                    ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300'
                    : currentQuestion.difficulty === 'hard'
                    ? 'bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300'
                    : 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300'
                }`}
              >
                {currentQuestion.difficulty}
              </span>
            </div>
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white leading-snug">
            {currentQuestion.question}
          </h2>

          {currentQuestion.citations && currentQuestion.citations.length > 0 && (
            <details className="text-xs text-slate-500 dark:text-slate-400 pt-1 group">
              <summary className="cursor-pointer font-bold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1.5 list-none">
                <BookOpen className="w-4 h-4" />
                <span>View Grounded RAG Citations ({currentQuestion.citations.length})</span>
              </summary>
              <div className="mt-2.5 space-y-2 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-navy-750">
                {currentQuestion.citations.map((c, i) => (
                  <div key={i} className="text-[11px] leading-relaxed border-b border-slate-200 dark:border-navy-750 last:border-0 pb-2 last:pb-0">
                    <span className="font-bold text-slate-800 dark:text-slate-200 capitalize">
                      [{c.source.replace('_', ' ')} - Page {c.page}]:
                    </span>{' '}
                    <span className="font-mono text-slate-700 dark:text-slate-300">{c.text}</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {/* Answer Recording and Text Input */}
      {!feedback && (
        <div className="space-y-4">
          {session.config.answer_method !== 'text' && (
            <AudioRecorder
              sessionId={sessionId}
              onTranscriptionComplete={handleTranscriptionComplete}
              disabled={submittingAnswer}
            />
          )}

          <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>Your Answer Response</span>
              </label>
              {transcriptEdited && (
                <span className="text-[11px] text-amber-600 dark:text-amber-400 font-bold">
                  (Edited transcript)
                </span>
              )}
            </div>

            <textarea
              rows={6}
              value={answerText}
              onChange={handleAnswerTextChange}
              placeholder="Record your voice answer above or type your architectural design, implementation details, and technical trade-offs here..."
              disabled={submittingAnswer}
              className="w-full rounded-xl border border-slate-300 dark:border-navy-700 bg-white dark:bg-navy-900 p-3.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono leading-relaxed resize-none"
            />

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {answerText.trim() ? `${answerText.trim().split(/\s+/).length} words` : '0 words'}
              </span>

              <button
                type="button"
                onClick={handleSubmitAnswer}
                disabled={submittingAnswer || !answerText.trim()}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md shadow-indigo-600/30 active:scale-95 cursor-pointer"
              >
                {submittingAnswer ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Scoring Answer with Gemini...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Submit & Score Answer</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Answer Scoring Feedback Panel */}
      {feedback && (
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-navy-800 pb-4">
            <div>
              <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Question Score
              </span>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
                  {feedback.score} <span className="text-base text-slate-400">/ 10</span>
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    feedback.score >= 8
                      ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60'
                      : feedback.score <= 4
                      ? 'bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-700/60'
                      : 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700/60'
                  }`}
                >
                  {feedback.score >= 8
                    ? 'Mastery Level'
                    : feedback.score <= 4
                    ? 'Foundations Needed'
                    : 'Solid Progress'}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleNextOrFinish}
              disabled={generatingNextQ}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-95 transition-all shadow-md shadow-indigo-600/30 self-start sm:self-auto cursor-pointer"
            >
              {generatingNextQ ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Preparing Next Adaptive Question...</span>
                </>
              ) : isLastQuestion ? (
                <>
                  <span>Complete Interview & View Report</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Next Adaptive Question</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800/60 space-y-2">
              <h4 className="text-xs font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Demonstrated Strengths</span>
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-800 dark:text-slate-200">
                {feedback.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">&bull;</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800/60 space-y-2">
              <h4 className="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Missing Points & Growth Areas</span>
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-800 dark:text-slate-200">
                {feedback.gaps.map((g, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">&bull;</span>
                    <span>{g}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {feedback.model_answer && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-navy-750 space-y-2">
              <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>10/10 Production Model Answer</span>
              </h4>
              <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-mono whitespace-pre-wrap bg-white dark:bg-navy-950 p-3.5 rounded-lg border border-slate-200 dark:border-navy-750">
                {feedback.model_answer}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
