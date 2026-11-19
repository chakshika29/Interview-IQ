import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Sparkles,
  Loader2,
  Trash2,
  FileCheck,
} from 'lucide-react';
import { api } from '../services/api';
import type { DocumentPreview } from '../types';

interface DocumentsPageProps {
  onDocumentsReady?: (resumeText: string, jobText: string) => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({ onDocumentsReady }) => {
  const navigate = useNavigate();

  // Resume state
  const [resumeText, setResumeText] = useState<string>('');
  const [resumePreview, setResumePreview] = useState<DocumentPreview | null>(null);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);

  // Job Description state
  const [jdTab, setJdTab] = useState<'paste' | 'upload'>('paste');
  const [jdPastedText, setJdPastedText] = useState<string>('');
  const [jdText, setJdText] = useState<string>('');
  const [jdPreview, setJdPreview] = useState<DocumentPreview | null>(null);
  const [jdLoading, setJdLoading] = useState(false);
  const [jdError, setJdError] = useState<string | null>(null);

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setResumeLoading(true);
    setResumeError(null);

    try {
      const res = await api.uploadResume(file);
      setResumeText(res.text);
      setResumePreview(res.preview);
    } catch (err: any) {
      console.error('Resume upload error:', err);
      setResumeError(err.response?.data?.detail || 'Failed to parse resume document.');
    } finally {
      setResumeLoading(false);
    }
  };

  const handleJdFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setJdLoading(true);
    setJdError(null);

    try {
      const res = await api.uploadJobDescriptionFile(file);
      setJdText(res.text);
      setJdPreview(res.preview);
    } catch (err: any) {
      console.error('JD upload error:', err);
      setJdError(err.response?.data?.detail || 'Failed to parse job description file.');
    } finally {
      setJdLoading(false);
    }
  };

  const handleJdPasteSubmit = async () => {
    if (!jdPastedText.trim()) {
      setJdError('Please paste the job description text.');
      return;
    }

    setJdLoading(true);
    setJdError(null);

    try {
      const res = await api.pasteJobDescription(jdPastedText);
      setJdText(res.text);
      setJdPreview(res.preview);
    } catch (err: any) {
      console.error('JD paste error:', err);
      setJdError(err.response?.data?.detail || 'Failed to process job description text.');
    } finally {
      setJdLoading(false);
    }
  };

  const handleLoadSampleData = () => {
    const sampleResume = `SENIOR AI ENGINEER & AGENT ARCHITECT
Candidate with 6+ years designing distributed LLM systems, RAG retrieval pipelines, and stateful multi-agent architectures.

TECHNICAL SKILLS:
- Languages & Frameworks: Python 3.12, FastAPI, LangGraph, LangChain, PyTorch, React.js, TypeScript
- Vector Databases & RAG: ChromaDB, Pinecone, Reciprocal Rank Fusion (RRF), BM25, Sentence-Transformers
- Agentic Patterns: Cyclic execution graphs, state checkpointing, human-in-the-loop validation, tool calling
- Infrastructure & Deployment: Docker, Kubernetes, AWS ECS, Uvicorn, PostgreSQL, Redis

SELECTED EXPERIENCE:
1. Lead AI Engineer at DataScale Inc (2022-Present):
   - Architected production RAG platform indexing 50,000+ technical documents using ChromaDB with cosine distance and BM25 hybrid fusion.
   - Implemented persistent graph checkpointers in LangGraph to guarantee fault-tolerant agent state recovery across network drops.
   - Reduced hallucination rates by 42% through structured context validation and semantic boundary chunking.
2. High-Throughput FastAPI Inference Microservice:
   - Engineered asynchronous REST backend handling 1,200 requests/min with sub-180ms P95 latency and automated Pydantic schema validation.`;

    const sampleJd = `STAFF AI PLATFORM ENGINEER - CORE AGENTIC SYSTEMS
We are seeking a Staff AI Engineer to spearhead our next-generation mock interview agent platform.

RESPONSIBILITIES:
- Architect and deploy production-grade Retrieval-Augmented Generation (RAG) engines combining dense vector search and sparse lexical retrieval.
- Build resilient, cyclic agent workflows with state checkpointing and dynamic failure recovery using LangGraph.
- Develop high-performance, asynchronous REST APIs in FastAPI with strict Pydantic validation and microservice containerization.
- Conduct empirical evaluations (MRR, Hit@K, LLM-as-a-judge) to quantify retrieval precision and eliminate model hallucinations.
- Implement multimodal audio transcription pipelines and real-time streaming interfaces.

REQUIRED QUALIFICATIONS:
- 5+ years of software engineering with deep expertise in Python, FastAPI, and distributed systems.
- Deep hands-on experience with vector databases (ChromaDB / pgvector) and hybrid search (BM25 + Dense RRF).
- Demonstrated mastery of agentic state persistence, tool calling, and checkpointer architectures.
- Deep familiarity with Google Gemini SDK, LLM evaluation metrics, and audio transcription interfaces.`;

    setResumeText(sampleResume);
    setResumePreview({
      word_count: sampleResume.split(/\s+/).length,
      char_count: sampleResume.length,
      line_count: sampleResume.split('\n').length,
      detected_sections: ['TECHNICAL SKILLS', 'SELECTED EXPERIENCE'],
      preview_snippet: sampleResume.slice(0, 350) + '...',
    });
    setResumeError(null);

    setJdText(sampleJd);
    setJdPastedText(sampleJd);
    setJdPreview({
      word_count: sampleJd.split(/\s+/).length,
      char_count: sampleJd.length,
      line_count: sampleJd.split('\n').length,
      detected_sections: ['RESPONSIBILITIES', 'REQUIRED QUALIFICATIONS'],
      preview_snippet: sampleJd.slice(0, 350) + '...',
    });
    setJdError(null);
  };

  const isReadyToProceed = Boolean(resumeText && jdText);

  const handleProceed = () => {
    sessionStorage.setItem('interviewiq_resume_text', resumeText);
    sessionStorage.setItem('interviewiq_jd_text', jdText);
    if (onDocumentsReady) {
      onDocumentsReady(resumeText, jdText);
    }
    navigate('/configure');
  };

  return (
    <div className="space-y-6 sm:space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-navy-700">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Document Ingestion & Analysis
          </h1>
          <p className="text-sm text-slate-600 dark:text-[#CBD5E1] mt-1">
            Provide your candidate resume and target job description to ground the AI mock interview in real context.
          </p>
        </div>
        <button
          type="button"
          onClick={handleLoadSampleData}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold text-violet-900 dark:text-violet-200 bg-violet-50 dark:bg-violet-950/70 border border-violet-200 dark:border-violet-700/80 hover:bg-violet-100 dark:hover:bg-violet-900/60 transition-colors shadow-xs self-start sm:self-auto cursor-pointer"
        >
          <Sparkles className="w-4 h-4 text-violet-600 dark:text-violet-400" />
          <span>Load AI Engineer Sample Data</span>
        </button>
      </div>

      {/* Two Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resume Card */}
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <span>1. Candidate Resume</span>
            </h2>
            {resumeText && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Extracted</span>
              </span>
            )}
          </div>

          <p className="text-xs text-slate-600 dark:text-[#CBD5E1]">
            Upload your technical resume in PDF, DOCX, or TXT format.
          </p>

          {resumeError && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{resumeError}</span>
            </div>
          )}

          {!resumeText ? (
            <label className="border-2 border-dashed border-slate-300 dark:border-navy-700 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-slate-50/50 dark:hover:bg-navy-800/40 transition-all">
              <UploadCloud className="w-10 h-10 text-slate-400 dark:text-slate-500 mb-2" />
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {resumeLoading ? 'Extracting document text...' : 'Click to upload resume'}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">PDF, DOCX, or TXT (Max 10MB)</span>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleResumeUpload}
                disabled={resumeLoading}
                className="hidden"
              />
              {resumeLoading && <Loader2 className="w-5 h-5 animate-spin text-indigo-500 mt-3" />}
            </label>
          ) : (
            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-200">
                  <span className="font-bold">Resume Extraction Summary</span>
                  <button
                    type="button"
                    onClick={() => {
                      setResumeText('');
                      setResumePreview(null);
                    }}
                    className="text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Replace</span>
                  </button>
                </div>
                {resumePreview && (
                  <div className="grid grid-cols-3 gap-2 py-2 text-center border-y border-slate-200 dark:border-navy-700 text-xs">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Words</span>
                      <span className="font-bold text-slate-900 dark:text-white">{resumePreview.word_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Characters</span>
                      <span className="font-bold text-slate-900 dark:text-white">{resumePreview.char_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Sections</span>
                      <span className="font-bold text-slate-900 dark:text-white">{resumePreview.detected_sections.length || 'N/A'}</span>
                    </div>
                  </div>
                )}
                <p className="text-[11px] font-mono text-slate-700 dark:text-slate-200 max-h-32 overflow-y-auto leading-relaxed bg-white dark:bg-navy-900 p-2.5 rounded-lg border border-slate-200 dark:border-navy-750">
                  {resumePreview?.preview_snippet || resumeText.slice(0, 300) + '...'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Job Description Card */}
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-violet-600 dark:text-violet-400" />
              <span>2. Job Description</span>
            </h2>
            {jdText && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Extracted</span>
              </span>
            )}
          </div>

          {!jdText && (
            <div className="flex items-center gap-2 border-b border-slate-200 dark:border-navy-700 pb-2">
              <button
                type="button"
                onClick={() => setJdTab('paste')}
                className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors ${
                  jdTab === 'paste'
                    ? 'bg-indigo-50 dark:bg-navy-800 text-indigo-600 dark:text-indigo-400'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Paste Text
              </button>
              <button
                type="button"
                onClick={() => setJdTab('upload')}
                className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors ${
                  jdTab === 'upload'
                    ? 'bg-indigo-50 dark:bg-navy-800 text-indigo-600 dark:text-indigo-400'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Upload File (PDF/DOCX)
              </button>
            </div>
          )}

          {jdError && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{jdError}</span>
            </div>
          )}

          {!jdText ? (
            jdTab === 'paste' ? (
              <div className="space-y-3">
                <textarea
                  rows={6}
                  value={jdPastedText}
                  onChange={(e) => setJdPastedText(e.target.value)}
                  placeholder="Paste the job requirements, responsibilities, and technical qualifications here..."
                  className="w-full rounded-xl border border-slate-300 dark:border-navy-700 bg-white dark:bg-navy-900 px-3.5 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono leading-relaxed resize-none"
                />
                <button
                  type="button"
                  onClick={handleJdPasteSubmit}
                  disabled={jdLoading || !jdPastedText.trim()}
                  className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm cursor-pointer"
                >
                  {jdLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                  <span>Validate & Save Job Description</span>
                </button>
              </div>
            ) : (
              <label className="border-2 border-dashed border-slate-300 dark:border-navy-700 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-slate-50/50 dark:hover:bg-navy-800/40 transition-all">
                <UploadCloud className="w-10 h-10 text-slate-400 dark:text-slate-500 mb-2" />
                <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {jdLoading ? 'Extracting document text...' : 'Click to upload job description'}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">PDF, DOCX, or TXT (Max 10MB)</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleJdFileUpload}
                  disabled={jdLoading}
                  className="hidden"
                />
                {jdLoading && <Loader2 className="w-5 h-5 animate-spin text-indigo-500 mt-3" />}
              </label>
            )
          ) : (
            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-200">
                  <span className="font-bold">Job Description Summary</span>
                  <button
                    type="button"
                    onClick={() => {
                      setJdText('');
                      setJdPreview(null);
                      setJdPastedText('');
                    }}
                    className="text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Replace</span>
                  </button>
                </div>
                {jdPreview && (
                  <div className="grid grid-cols-3 gap-2 py-2 text-center border-y border-slate-200 dark:border-navy-700 text-xs">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Words</span>
                      <span className="font-bold text-slate-900 dark:text-white">{jdPreview.word_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Characters</span>
                      <span className="font-bold text-slate-900 dark:text-white">{jdPreview.char_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block text-[10px] font-semibold uppercase">Sections</span>
                      <span className="font-bold text-slate-900 dark:text-white">{jdPreview.detected_sections.length || 'N/A'}</span>
                    </div>
                  </div>
                )}
                <p className="text-[11px] font-mono text-slate-700 dark:text-slate-200 max-h-32 overflow-y-auto leading-relaxed bg-white dark:bg-navy-900 p-2.5 rounded-lg border border-slate-200 dark:border-navy-750">
                  {jdPreview?.preview_snippet || jdText.slice(0, 300) + '...'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="p-5 rounded-2xl bg-white dark:bg-navy-850 border border-slate-200 dark:border-navy-700 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-xs text-slate-600 dark:text-[#CBD5E1]">
          {isReadyToProceed ? (
            <span className="text-emerald-700 dark:text-emerald-400 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Both documents verified and parsed! Ready to configure interview.</span>
            </span>
          ) : (
            <span>Please provide both your Resume and the Job Description to continue.</span>
          )}
        </div>
        <button
          type="button"
          onClick={handleProceed}
          disabled={!isReadyToProceed}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-indigo-600/30 cursor-pointer"
        >
          <span>Continue to Configuration</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
