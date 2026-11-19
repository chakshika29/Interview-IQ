import React, { useEffect, useState } from 'react';
import {
  Cpu,
  ShieldCheck,
  Moon,
  Sun,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Play,
} from 'lucide-react';
import { api } from '../services/api';
import type { AIHealthStatus } from '../types';

interface SettingsPageProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ darkMode, setDarkMode }) => {
  const [aiHealth, setAiHealth] = useState<AIHealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [testingCall, setTestingCall] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    checkStatus(false);
  }, []);

  const checkStatus = async (runTest: boolean) => {
    if (runTest) setTestingCall(true);
    else setLoadingHealth(true);

    try {
      const data = await api.getAIHealth(runTest);
      setAiHealth(data);
      if (runTest && data.test_call) {
        setTestResult(data.test_call);
      }
    } catch (err) {
      console.error('Failed to query AI health:', err);
    } finally {
      setLoadingHealth(false);
      setTestingCall(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <div className="pb-4 border-b border-slate-200 dark:border-navy-700">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
          System Settings & AI Diagnostics
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Monitor Google GenAI connectivity, model fallbacks, latency metrics, and user preferences.
        </p>
      </div>

      <div className="space-y-6">
        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-navy-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-950 flex items-center justify-center text-primary-600 dark:text-primary-400">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Google GenAI Client Status</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Gemini LLM & Embedding Service Engine</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => checkStatus(true)}
              disabled={testingCall}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 transition-all shadow-sm active:scale-95"
            >
              {testingCall ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Probing API...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Live Diagnostic Test</span>
                </>
              )}
            </button>
          </div>

          {loadingHealth ? (
            <div className="py-6 flex items-center justify-center space-y-2 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
            </div>
          ) : aiHealth ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-1">
                <span className="text-slate-400 font-medium block">API Key Status</span>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 font-semibold ${
                      aiHealth.key_present ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {aiHealth.key_present ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{aiHealth.key_present ? 'Configured & Active' : 'Missing in .env'}</span>
                  </span>
                  {aiHealth.key_masked && (
                    <span className="font-mono text-slate-500 text-[11px]">({aiHealth.key_masked})</span>
                  )}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-1">
                <span className="text-slate-400 font-medium block">Primary Generation Model</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {aiHealth.primary_model}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-1">
                <span className="text-slate-400 font-medium block">Fallback Models Cascade</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {aiHealth.fallback_models.join(', ')}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 space-y-1">
                <span className="text-slate-400 font-medium block">Dense Embedding Model</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {aiHealth.embed_model} (3072-dim Cosine)
                </span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-rose-500">Failed to connect to backend AI diagnostic endpoint.</p>
          )}

          {testResult && (
            <div
              className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                testResult.status === 'success'
                  ? 'bg-emerald-50/70 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-rose-50/70 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300'
              }`}
            >
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center gap-1.5">
                  {testResult.status === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-rose-600" />
                  )}
                  <span>Live Probe Result: {testResult.status.toUpperCase()}</span>
                </span>
                <span>Latency: {testResult.latency_ms} ms</span>
              </div>
              {testResult.response && (
                <p className="font-mono text-[11px]">Model Output: &quot;{testResult.response}&quot; on {testResult.active_model}</p>
              )}
              {testResult.error && (
                <p className="font-mono text-[11px] text-rose-600">Error: {testResult.error}</p>
              )}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-850 p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white">Interface & Preferences</h2>
          <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-navy-800">
            <div>
              <span className="text-xs font-semibold text-slate-900 dark:text-white block">Theme Mode</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Switch between dark navy and light SaaS theme</span>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-navy-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
            >
              {darkMode ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-slate-600" />}
              <span>{darkMode ? 'Dark Theme' : 'Light Theme'}</span>
            </button>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <span className="text-xs font-semibold text-slate-900 dark:text-white block">Local Session Isolation</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Per-interview ChromaDB collections guarantee zero cross-contamination</span>
            </div>
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              <span>Enforced</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
