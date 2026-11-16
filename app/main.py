import os
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.generator import (
    extract_skill_gap,
    generate_adaptive_question,
    generate_question,
    score_answer,
)
from app.ingest import load_document, split_text_by_boundaries
from app.retriever import Retriever
from app.schemas import Chunk, Feedback, Question, SkillGap

# WHY: FastAPI provides automatic Swagger documentation (/docs), input validation via Pydantic,
# and high-performance asynchronous API endpoints.
app = FastAPI(
    title="InterviewIQ API",
    description="Production REST API for RAG-based AI Engineer interview preparation and skill gap analysis.",
    version="1.0.0",
)

# WHY: In-memory application state holds the active Retriever instance across requests.
# In a distributed multi-tenant production system, this could be backed by Redis or ChromaDB server.
app_state: dict[str, Retriever | None] = {"retriever": None}


def get_or_create_retriever() -> Retriever:
    """Helper to ensure an initialized retriever exists."""
    if app_state["retriever"] is None:
        r = Retriever()
        # Pre-seed with bundled sample documents if present
        if os.path.exists("data/job.txt") and os.path.exists("data/resume.pdf"):
            jd = load_document("data/job.txt", "job_description")
            res = load_document("data/resume.pdf", "resume")
            r.add(jd + res)
        app_state["retriever"] = r
    return app_state["retriever"]


# ---------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------
class AnalyzeRequest(BaseModel):
    job_text: str | None = Field(None, description="Raw text of the target job description.")
    resume_text: str | None = Field(None, description="Raw text of the candidate's resume.")
    use_sample_data: bool = Field(True, description="Whether to fallback to data/ samples if text is omitted.")


class AnalyzeResponse(BaseModel):
    status: str
    skill_gap: SkillGap
    total_chunks: int


class QuestionRequest(BaseModel):
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    last_topic: str | None = None
    last_score: int | None = Field(None, ge=1, le=10)


class ScoreRequest(BaseModel):
    question: str
    topic: str = ""
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    answer: str


class ScoreResponse(BaseModel):
    feedback: Feedback
    citations: list[dict]


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------
@app.get("/health", tags=["Monitoring"])
def health_check():
    """
    Health check endpoint for Docker container orchestration and uptime monitors.

    WHY: Container platforms (like Kubernetes or AWS ECS) probe /health to verify
    readiness before routing traffic to the instance.
    """
    return {
        "status": "healthy",
        "service": "InterviewIQ API",
        "version": "1.0.0",
        "retriever_ready": app_state["retriever"] is not None,
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Interview Prep"])
def analyze_documents(req: AnalyzeRequest):
    """
    Ingest job description and resume, index into ChromaDB vector store, and return skill gap analysis.

    WHY: Diagnoses matched vs missing competencies to set up the personalized interview session.
    """
    jd_chunks = []
    resume_chunks = []

    # Process supplied raw text or fallback to bundled sample files
    if req.job_text:
        for i, text in enumerate(split_text_by_boundaries(req.job_text)):
            jd_chunks.append(Chunk(id=f"api-jd-{i}", text=text, source="job_description", page=1))
    elif req.use_sample_data and os.path.exists("data/job.txt"):
        jd_chunks = load_document("data/job.txt", "job_description")

    if req.resume_text:
        for i, text in enumerate(split_text_by_boundaries(req.resume_text)):
            resume_chunks.append(Chunk(id=f"api-res-{i}", text=text, source="resume", page=1))
    elif req.use_sample_data and os.path.exists("data/resume.pdf"):
        resume_chunks = load_document("data/resume.pdf", "resume")

    if not jd_chunks or not resume_chunks:
        raise HTTPException(
            status_code=400,
            detail="Both job description and resume must be provided via raw text or bundled sample files.",
        )

    # Initialize fresh retriever and index documents
    retriever = Retriever()
    retriever.add(jd_chunks + resume_chunks)
    app_state["retriever"] = retriever

    # Extract skill gap via Gemini structured output
    skill_gap = extract_skill_gap(jd_chunks, resume_chunks)

    return AnalyzeResponse(
        status="success",
        skill_gap=skill_gap,
        total_chunks=len(jd_chunks) + len(resume_chunks),
    )


@app.post("/question", response_model=Question, tags=["Interview Prep"])
def get_interview_question(req: QuestionRequest):
    """
    Generate an interview question targeted at the candidate's resume and job requirements.
    Supports adaptive progression if previous score is provided.

    WHY: Tailors the mock interview loop dynamically to test either edge cases (if last score was high)
    or foundational fundamentals (if last score was low).
    """
    retriever = get_or_create_retriever()

    if req.last_score is not None:
        last_q = Question(
            question="",
            topic=req.last_topic or "AI Engineering",
            difficulty=req.difficulty,
        )
        last_fb = Feedback(
            score=req.last_score,
            strengths=[],
            gaps=[],
            model_answer="",
        )
        return generate_adaptive_question(
            retriever,
            last_question=last_q,
            last_feedback=last_fb,
            current_difficulty=req.difficulty,
        )

    return generate_question(retriever, difficulty=req.difficulty)


@app.post("/score", response_model=ScoreResponse, tags=["Interview Prep"])
def score_candidate_answer(req: ScoreRequest):
    """
    Score a candidate's answer against retrieved ground truth job requirements.

    WHY: Evaluates answers objectively (1-10) with actionable strengths, gaps,
    a 10/10 model answer, and source citations for total transparency.
    """
    retriever = get_or_create_retriever()

    question_obj = Question(
        question=req.question,
        topic=req.topic,
        difficulty=req.difficulty,
    )

    feedback = score_answer(retriever, question_obj, req.answer)
    citations = retriever.search(f"{req.topic} {req.question}", k=3, mode="hybrid")

    return ScoreResponse(
        feedback=feedback,
        citations=citations,
    )
