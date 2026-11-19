from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core Ingestion & Retrieval Schemas (Preserved for full backward-compat)
# ---------------------------------------------------------------------------
class Chunk(BaseModel):
    id: str
    text: str
    source: Literal["resume", "job_description"]
    page: int | None = None


class Feedback(BaseModel):
    score: int = Field(ge=1, le=10)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    model_answer: str = ""


class Question(BaseModel):
    question: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]


class SkillGap(BaseModel):
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Upgraded Production Interview Schemas
# ---------------------------------------------------------------------------
InterviewType = Literal["technical", "hr", "behavioral", "mixed"]
InterviewDifficulty = Literal["beginner", "intermediate", "advanced", "adaptive"]
AnswerMethod = Literal["voice", "text", "voice_text"]


class InterviewConfig(BaseModel):
    interview_type: InterviewType = "technical"
    difficulty: InterviewDifficulty = "adaptive"
    num_questions: int = Field(5, ge=1, le=25)
    answer_method: AnswerMethod = "voice_text"
    time_limit_seconds: int = Field(120, ge=30, le=600)
    enable_followup: bool = True
    enable_video: bool = False
    enable_detailed_feedback: bool = True


class QuestionDetail(BaseModel):
    id: str
    question: str
    topic: str
    difficulty: str
    category: str = "Technical"
    relevant_skills: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class DetailedFeedback(BaseModel):
    score: int = Field(ge=1, le=10)
    relevance_score: int = Field(7, ge=1, le=10)
    technical_correctness_score: int = Field(7, ge=1, le=10)
    completeness_score: int = Field(7, ge=1, le=10)
    communication_clarity_score: int = Field(7, ge=1, le=10)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    technical_corrections: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    model_answer: str = ""
    recommended_followup_topics: list[str] = Field(default_factory=list)


class AnswerAttempt(BaseModel):
    attempt_id: str
    question_id: str
    question_text: str
    topic: str
    difficulty: str
    answer_text: str
    audio_filename: str | None = None
    original_transcript: str | None = None
    transcript_edited: bool = False
    feedback: DetailedFeedback
    created_at: str


class SessionData(BaseModel):
    id: str
    created_at: str
    updated_at: str
    status: Literal["created", "in_progress", "completed"] = "created"
    config: InterviewConfig
    skill_gap: SkillGap | None = None
    questions: list[QuestionDetail] = Field(default_factory=list)
    answers: list[AnswerAttempt] = Field(default_factory=list)
    current_question_index: int = 0
    total_chunks: int = 0
    resume_preview: dict[str, Any] | None = None
    jd_preview: dict[str, Any] | None = None
    overall_score: float | None = None
    completion_summary: dict[str, Any] | None = None


class CreateSessionRequest(BaseModel):
    job_text: str | None = None
    resume_text: str | None = None
    use_sample_data: bool = False
    config: InterviewConfig = Field(default_factory=InterviewConfig)


class AnswerSubmission(BaseModel):
    question_id: str
    answer_text: str
    audio_filename: str | None = None
    original_transcript: str | None = None
    transcript_edited: bool = False


class TranscriptionResponse(BaseModel):
    transcript: str
    audio_filename: str
    mime_type: str
    duration_estimate_sec: float | None = None
