import axios from 'axios';
import type {
  AIHealthStatus,
  AnswerAttempt,
  DocumentPreview,
  InterviewConfig,
  QuestionDetail,
  SessionData,
  SessionSummary,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
});

export const api = {
  // Health & Diagnostics
  getHealth: async () => {
    const res = await client.get('/api/v1/health');
    return res.data;
  },

  getAIHealth: async (testCall: boolean = false): Promise<AIHealthStatus> => {
    const res = await client.get('/api/v1/health/ai', {
      params: { test_call: testCall },
    });
    return res.data;
  },

  // Document Ingestion
  uploadResume: async (file: File): Promise<{ status: string; filename: string; text: string; preview: DocumentPreview }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/api/v1/documents/resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  uploadJobDescriptionFile: async (file: File): Promise<{ status: string; filename: string; text: string; preview: DocumentPreview }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/api/v1/documents/job-description', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  pasteJobDescription: async (rawText: string): Promise<{ status: string; filename: string; text: string; preview: DocumentPreview }> => {
    const formData = new FormData();
    formData.append('raw_text', rawText);
    const res = await client.post('/api/v1/documents/job-description', formData);
    return res.data;
  },

  // Interview Sessions
  createSession: async (payload: {
    resume_text?: string;
    job_text?: string;
    use_sample_data?: boolean;
    config: InterviewConfig;
  }): Promise<SessionData> => {
    const res = await client.post('/api/v1/interviews', payload);
    return res.data;
  },

  listSessions: async (): Promise<SessionSummary[]> => {
    const res = await client.get('/api/v1/interviews');
    return res.data;
  },

  getSession: async (sessionId: string): Promise<SessionData> => {
    const res = await client.get(`/api/v1/interviews/${sessionId}`);
    return res.data;
  },

  getNextQuestion: async (sessionId: string): Promise<QuestionDetail> => {
    const res = await client.post(`/api/v1/interviews/${sessionId}/next-question`);
    return res.data;
  },

  transcribeAudio: async (sessionId: string, audioBlob: Blob): Promise<{ transcript: string; audio_filename: string; mime_type: string }> => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    const res = await client.post(`/api/v1/interviews/${sessionId}/transcribe`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  submitAnswer: async (
    sessionId: string,
    payload: {
      question_id: string;
      answer_text: string;
      audio_filename?: string | null;
      original_transcript?: string | null;
      transcript_edited?: boolean;
    }
  ): Promise<AnswerAttempt> => {
    const res = await client.post(`/api/v1/interviews/${sessionId}/answers`, payload);
    return res.data;
  },

  completeInterview: async (sessionId: string): Promise<SessionData> => {
    const res = await client.post(`/api/v1/interviews/${sessionId}/complete`);
    return res.data;
  },

  getReportUrl: (sessionId: string) => {
    return `${API_BASE_URL}/api/v1/interviews/${sessionId}/report`;
  },
};
