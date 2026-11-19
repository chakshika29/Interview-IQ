import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Mic,
  Database,
  FileCheck2,
  CheckCircle2,
  Zap,
  Play,
  LayoutDashboard,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-10 sm:space-y-12 py-3 sm:py-5 pb-16">
      {/* Hero Section */}
      <section className="relative text-center max-w-4xl mx-auto px-4 pt-2 sm:pt-4">
        {/* High-Contrast Hero Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-violet-50 text-violet-900 border border-violet-200/90 dark:bg-violet-950/80 dark:text-violet-200 dark:border-violet-700/80 mb-3 sm:mb-4 shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-violet-600 dark:text-violet-400" />
          <span>Next-Generation AI Interview Preparation</span>
        </div>

        {/* Primary Hero Heading: Pure White #FFFFFF in dark mode, deep slate #0F172A in light mode */}
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-[#FFFFFF] leading-[1.2]">
          Master High-Stakes AI Interviews with{' '}
          <span className="bg-gradient-to-r from-violet-600 via-indigo-600 to-purple-600 dark:from-violet-400 dark:via-indigo-300 dark:to-fuchsia-300 bg-clip-text text-transparent">
            Adaptive Hybrid RAG
          </span>
        </h1>

        {/* Supporting Description: Readable Light Slate #CBD5E1 in dark mode */}
        <p className="mt-3 sm:mt-4 text-sm sm:text-base lg:text-lg text-slate-600 dark:text-[#CBD5E1] max-w-2xl mx-auto leading-relaxed">
          Ground mock interviews directly in your real resume projects and target job requirements.
          Simulate live voice answering, get objective 1-10 scoring, and adapt dynamically to your knowledge gaps.
        </p>

        {/* Prominent, Above-the-Fold Call-To-Action Buttons */}
        <div className="mt-6 sm:mt-7 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
          <Link
            to="/documents"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm sm:text-base font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-95 shadow-md shadow-indigo-600/30 transition-all hover:shadow-lg hover:shadow-indigo-600/40"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Start Mock Interview</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm sm:text-base font-semibold text-slate-700 dark:text-slate-100 bg-white dark:bg-navy-800 hover:bg-slate-100 dark:hover:bg-navy-700 border border-slate-300 dark:border-navy-600 shadow-xs transition-all"
          >
            <LayoutDashboard className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <span>View Dashboard</span>
          </Link>
        </div>

        {/* Bottom Feature Labels: Light Gray #CBD5E1 in dark mode */}
        <div className="mt-6 sm:mt-7 pt-4 sm:pt-5 border-t border-slate-200/80 dark:border-navy-800/80 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-semibold text-slate-700 dark:text-[#CBD5E1]">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>ChromaDB + BM25 RRF Hybrid Search</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>Google Gemini Flash & Embeddings</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>Live Microphone Voice & STT</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>Downloadable PDF Performance Reports</span>
          </div>
        </div>
      </section>

      {/* Feature Grid Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8 sm:mb-10">
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900 dark:text-white">
            Architected for Realistic Technical Evaluations
          </h2>
          <p className="mt-1.5 text-xs sm:text-sm text-slate-600 dark:text-[#CBD5E1]">
            Generic interview bots ask textbook questions. InterviewIQ simulates an actual principal engineer interview.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs hover:shadow-md transition-shadow space-y-3">
            <div className="w-11 h-11 rounded-xl bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/60 dark:border-indigo-800/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Precision Ingestion</h3>
            <p className="text-xs text-slate-600 dark:text-[#CBD5E1] leading-relaxed">
              Sentence-boundary chunking respects grammatical thought boundaries across PDF, DOCX, and TXT resumes and job posts.
            </p>
          </div>

          <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs hover:shadow-md transition-shadow space-y-3">
            <div className="w-11 h-11 rounded-xl bg-violet-50 dark:bg-violet-950/80 border border-violet-200/60 dark:border-violet-800/60 flex items-center justify-center text-violet-600 dark:text-violet-400">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Hybrid Retrieval (RRF)</h3>
            <p className="text-xs text-slate-600 dark:text-[#CBD5E1] leading-relaxed">
              Merges dense semantic vectors (<code className="text-indigo-600 dark:text-violet-300 font-mono">gemini-embedding-001</code>) with sparse BM25 lexical tokens for exact tool retrieval.
            </p>
          </div>

          <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs hover:shadow-md transition-shadow space-y-3">
            <div className="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/80 border border-amber-200/60 dark:border-amber-800/60 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Adaptive Difficulty</h3>
            <p className="text-xs text-slate-600 dark:text-[#CBD5E1] leading-relaxed">
              High scores advance to deeper architecture trade-offs; lower scores automatically drill down on the exact weak topic.
            </p>
          </div>

          <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs hover:shadow-md transition-shadow space-y-3">
            <div className="w-11 h-11 rounded-xl bg-rose-50 dark:bg-rose-950/80 border border-rose-200/60 dark:border-rose-800/60 flex items-center justify-center text-rose-600 dark:text-rose-400">
              <Mic className="w-5 h-5" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Voice & Transcription</h3>
            <p className="text-xs text-slate-600 dark:text-[#CBD5E1] leading-relaxed">
              Browser-native MediaRecorder records spoken responses, transcribes via Gemini multimodal audio STT, and enables candidate review.
            </p>
          </div>
        </div>
      </section>

      {/* Bottom CTA Card */}
      <section className="max-w-5xl mx-auto px-4">
        <div className="rounded-2xl sm:rounded-3xl p-6 sm:p-10 bg-gradient-to-tr from-navy-900 via-indigo-950 to-navy-950 text-white shadow-xl relative overflow-hidden border border-indigo-500/20">
          <div className="relative z-10 max-w-2xl space-y-3 sm:space-y-4">
            <h3 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white">
              Ready to Prepare for Your Next Senior AI Engineer Role?
            </h3>
            <p className="text-xs sm:text-sm text-[#CBD5E1] leading-relaxed">
              Upload your resume and test yourself against targeted questions derived directly from actual job postings.
            </p>
            <div className="pt-2">
              <Link
                to="/documents"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold text-slate-950 bg-white hover:bg-slate-100 shadow transition-colors"
              >
                <span>Upload Documents & Begin</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
