export type InterviewType = 'technical' | 'hr' | 'behavioral' | 'mixed';
export type InterviewDifficulty = 'beginner' | 'intermediate' | 'advanced' | 'adaptive';
export type AnswerMethod = 'voice' | 'text' | 'voice_text';

export interface InterviewConfig {
  interview_type: InterviewType;
  difficulty: InterviewDifficulty;
  num_questions: number;
  answer_method: AnswerMethod;
  time_limit_seconds: number;
  enable_followup: boolean;
  enable_video: boolean;
  enable_detailed_feedback: boolean;
}

export interface SkillGap {
  matched: string[];
  missing: string[];
}

export interface Citation {
  id: string;
  text: string;
  source: 'resume' | 'job_description';
  page: number;
  score?: number;
  rrf_score?: number;
}

export interface QuestionDetail {
  id: string;
  question: string;
  topic: string;
  difficulty: string;
  category: string;
  relevant_skills: string[];
  evaluation_criteria: string[];
  citations: Citation[];
}

export interface DetailedFeedback {
  score: number;
  relevance_score: number;
  technical_correctness_score: number;
  completeness_score: number;
  communication_clarity_score: number;
  strengths: string[];
  gaps: string[];
  technical_corrections: string[];
  improvement_suggestions: string[];
  model_answer: string;
  recommended_followup_topics: string[];
}

export interface AnswerAttempt {
  attempt_id: string;
  question_id: string;
  question_text: string;
  topic: string;
  difficulty: string;
  answer_text: string;
  audio_filename?: string | null;
  original_transcript?: string | null;
  transcript_edited: boolean;
  feedback: DetailedFeedback;
  created_at: string;
}

export interface DocumentPreview {
  word_count: number;
  char_count: number;
  line_count: number;
  detected_sections: string[];
  preview_snippet: string;
}

export interface SessionData {
  id: string;
  created_at: string;
  updated_at: string;
  status: 'created' | 'in_progress' | 'completed';
  config: InterviewConfig;
  skill_gap?: SkillGap | null;
  questions: QuestionDetail[];
  answers: AnswerAttempt[];
  current_question_index: number;
  total_chunks: number;
  resume_preview?: DocumentPreview | null;
  jd_preview?: DocumentPreview | null;
  overall_score?: number | null;
  completion_summary?: {
    average_score: number;
    total_completed: number;
    highest_score: number;
    lowest_score: number;
    topics_covered: string[];
  } | null;
}

export interface SessionSummary {
  id: string;
  created_at: string;
  updated_at: string;
  status: 'created' | 'in_progress' | 'completed';
  interview_type: string;
  difficulty: string;
  total_questions: number;
  completed_questions: number;
  average_score?: number | null;
}

export interface AIHealthStatus {
  configured: boolean;
  primary_model: string;
  fallback_models: string[];
  embed_model: string;
  key_present: boolean;
  key_masked?: string | null;
  status: string;
  test_call?: {
    status: string;
    latency_ms: number;
    response?: string;
    error?: string;
  };
}
