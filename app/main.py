import datetime
import os
import tempfile
import uuid
from typing import Any, Literal
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.generator import (
    extract_skill_gap,
    generate_adaptive_question,
    generate_question,
    get_next_difficulty,
    score_answer,
)
from app.ingest import (
    extract_document_preview,
    load_document,
    read_pages,
    split_text_by_boundaries,
    validate_document_content,
)
from app.retriever import Retriever
from app.schemas import (
    AnswerAttempt,
    AnswerSubmission,
    Chunk,
    CreateSessionRequest,
    DetailedFeedback,
    Feedback,
    InterviewConfig,
    Question,
    QuestionDetail,
    SessionData,
    SkillGap,
    TranscriptionResponse,
)
from app.services import audio_service, gemini_service, report_service, session_store

app = FastAPI(
    title="InterviewIQ API",
    description="Production REST API for RAG-based AI Engineer interview preparation, voice transcription, and skill gap analysis.",
    version="2.0.0",
)

# Enable CORS for React frontend (Vite dev server runs on port 5173 / 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy in-memory application state for backward compatibility
app_state: dict[str, Retriever | None] = {"retriever": None}


def get_or_create_retriever() -> Retriever:
    """Helper to ensure an initialized retriever exists for legacy endpoints."""
    if app_state["retriever"] is None:
        r = Retriever(session_id="legacy-global")
        if os.path.exists("data/job.txt") and os.path.exists("data/resume.pdf"):
            jd = load_document("data/job.txt", "job_description")
            res = load_document("data/resume.pdf", "resume")
            r.add(jd + res)
        elif os.path.exists("samples/sample_job.txt") and os.path.exists("samples/sample_resume.txt"):
            jd = load_document("samples/sample_job.txt", "job_description")
            res = load_document("samples/sample_resume.txt", "resume")
            r.add(jd + res)
        app_state["retriever"] = r
    return app_state["retriever"]


# ---------------------------------------------------------------------------
# Legacy Request & Response Models (Preserved)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Monitoring & Health Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Monitoring"])
@app.get("/api/v1/health", tags=["Monitoring"])
def health_check():
    """Health check endpoint for Docker container orchestration and uptime monitors."""
    return {
        "status": "healthy",
        "service": "InterviewIQ API",
        "version": "2.0.0",
        "retriever_ready": app_state["retriever"] is not None,
    }


@app.get("/api/v1/health/ai", tags=["Monitoring"])
def ai_health_diagnostic(test_call: bool = False):
    """
    Gemini connectivity diagnostic checking model availability, keys, and response latency.
    """
    return gemini_service.check_health(test_call=test_call)


# ---------------------------------------------------------------------------
# Document Ingestion Endpoints (Phase 4)
# ---------------------------------------------------------------------------
@app.post("/api/v1/documents/resume", tags=["Documents"])
async def upload_resume(file: UploadFile = File(...)):
    """Upload resume document (PDF, DOCX, TXT) and return extracted text and preview."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: .pdf, .docx, .txt",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds maximum 10MB limit.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        pages = read_pages(tmp_path)
        full_text = "\n\n".join(text for _, text in pages)
        validated_text = validate_document_content(full_text, filename=file.filename or "resume")
        preview = extract_document_preview(validated_text)
        return {
            "status": "success",
            "filename": file.filename,
            "text": validated_text,
            "preview": preview,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/v1/documents/job-description", tags=["Documents"])
async def upload_job_description(
    file: UploadFile | None = File(None),
    raw_text: str | None = Form(None),
):
    """Upload or paste a job description (PDF, DOCX, TXT or raw text)."""
    text_to_process = ""
    filename = "pasted_job_description.txt"

    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx", ".txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: .pdf, .docx, .txt",
            )
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds maximum 10MB limit.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            pages = read_pages(tmp_path)
            text_to_process = "\n\n".join(text for _, text in pages)
            filename = file.filename
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    elif raw_text:
        text_to_process = raw_text
    else:
        raise HTTPException(status_code=400, detail="Must provide either a file or raw_text.")

    try:
        validated_text = validate_document_content(text_to_process, filename=filename)
        preview = extract_document_preview(validated_text)
        return {
            "status": "success",
            "filename": filename,
            "text": validated_text,
            "preview": preview,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Session & Interview Endpoints (Phases 5, 6, 7, 8, 9, 10, 11)
# ---------------------------------------------------------------------------
@app.post("/api/v1/interviews", response_model=SessionData, tags=["Interview Sessions"])
def create_interview_session(req: CreateSessionRequest):
    """
    Initialize a new mock interview session with document indexing, session-isolated RAG,
    and automatic skill-gap extraction.
    """
    session_id = str(uuid.uuid4())
    jd_chunks = []
    resume_chunks = []
    resume_text = req.resume_text
    job_text = req.job_text

    # Handle sample fallbacks
    if not job_text and req.use_sample_data:
        if os.path.exists("data/job.txt"):
            with open("data/job.txt", encoding="utf-8") as f:
                job_text = f.read()
        elif os.path.exists("samples/sample_job.txt"):
            with open("samples/sample_job.txt", encoding="utf-8") as f:
                job_text = f.read()

    if not resume_text and req.use_sample_data:
        if os.path.exists("data/resume.pdf"):
            pages = read_pages("data/resume.pdf")
            resume_text = "\n\n".join(t for _, t in pages)
        elif os.path.exists("samples/sample_resume.txt"):
            with open("samples/sample_resume.txt", encoding="utf-8") as f:
                resume_text = f.read()

    if not job_text or not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Both Job Description and Resume must be provided to initiate an interview session.",
        )

    # Chunk documents
    for i, t in enumerate(split_text_by_boundaries(job_text)):
        jd_chunks.append(Chunk(id=f"{session_id}-jd-{i}", text=t, source="job_description", page=1))

    for i, t in enumerate(split_text_by_boundaries(resume_text)):
        resume_chunks.append(Chunk(id=f"{session_id}-res-{i}", text=t, source="resume", page=1))

    # Initialize isolated session retriever
    retriever = Retriever(session_id=session_id)
    retriever.add(jd_chunks + resume_chunks)
    session_store.set_retriever(session_id, retriever)

    # Extract skill gap via Gemini structured output
    try:
        skill_gap = extract_skill_gap(jd_chunks, resume_chunks)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI Skill Gap Analysis failed: {exc}")

    resume_preview = extract_document_preview(resume_text)
    jd_preview = extract_document_preview(job_text)

    # Persist session
    session = session_store.create_session(
        config=req.config,
        session_id=session_id,
        skill_gap=skill_gap,
        total_chunks=len(jd_chunks) + len(resume_chunks),
        resume_preview=resume_preview,
        jd_preview=jd_preview,
    )
    return session


@app.get("/api/v1/interviews", tags=["Interview Sessions"])
def list_interviews():
    """Retrieve history of all past interview sessions."""
    return session_store.list_sessions()


@app.get("/api/v1/interviews/{session_id}", response_model=SessionData, tags=["Interview Sessions"])
def get_interview(session_id: str):
    """Retrieve complete data for a specific interview session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return session


@app.post("/api/v1/interviews/{session_id}/next-question", response_model=QuestionDetail, tags=["Interview Sessions"])
def get_next_question(session_id: str):
    """
    Generate the next grounded interview question using RAG context, candidate background,
    and adaptive difficulty logic.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if len(session.questions) >= session.config.num_questions:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum question count ({session.config.num_questions}) reached for this session.",
        )

    retriever = session_store.get_retriever(session_id)

    # Determine difficulty level
    if session.config.difficulty == "adaptive" and session.answers:
        last_answer = session.answers[-1]
        last_q = Question(
            question=last_answer.question_text,
            topic=last_answer.topic,
            difficulty=last_answer.difficulty if last_answer.difficulty in ["easy", "medium", "hard"] else "medium",
        )
        last_fb = Feedback(
            score=last_answer.feedback.score,
            strengths=last_answer.feedback.strengths,
            gaps=last_answer.feedback.gaps,
            model_answer=last_answer.feedback.model_answer,
        )
        current_diff = last_q.difficulty
        generated_q = generate_adaptive_question(
            retriever,
            last_question=last_q,
            last_feedback=last_fb,
            current_difficulty=current_diff,
        )
    else:
        diff_str = (
            "medium"
            if session.config.difficulty in ["adaptive", "intermediate"]
            else ("easy" if session.config.difficulty == "beginner" else "hard")
        )
        generated_q = generate_question(retriever, difficulty=diff_str)

    # Fetch grounding citations
    citations = retriever.search(f"{generated_q.topic} {generated_q.question}", k=3, mode="hybrid")

    q_detail = QuestionDetail(
        id=f"q_{uuid.uuid4().hex[:8]}",
        question=generated_q.question,
        topic=generated_q.topic,
        difficulty=generated_q.difficulty,
        category=session.config.interview_type.capitalize(),
        relevant_skills=[generated_q.topic],
        evaluation_criteria=[
            "Technical accuracy and depth",
            "Clarity of explanation",
            "Handling of trade-offs and edge cases",
        ],
        citations=citations,
    )

    session.questions.append(q_detail)
    session.current_question_index = len(session.questions) - 1
    session.status = "in_progress"
    session_store.save_session(session)

    return q_detail


@app.post("/api/v1/interviews/{session_id}/transcribe", response_model=TranscriptionResponse, tags=["Voice & Audio"])
async def transcribe_interview_audio(
    session_id: str,
    file: UploadFile = File(...),
):
    """
    Save candidate's spoken answer recording to private storage and transcribe using Gemini Audio STT.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Empty or invalid audio data received.")

    mime_type = file.content_type or "audio/webm"
    filename, _ = audio_service.save_recording(session_id, audio_bytes, mime_type=mime_type)

    transcript = audio_service.transcribe(session_id, audio_bytes, mime_type=mime_type)

    return TranscriptionResponse(
        transcript=transcript,
        audio_filename=filename,
        mime_type=mime_type,
    )


@app.post("/api/v1/interviews/{session_id}/answers", response_model=AnswerAttempt, tags=["Interview Sessions"])
def submit_interview_answer(session_id: str, submission: AnswerSubmission):
    """
    Score a candidate's answer using Gemini + RAG rubric, returning detailed feedback,
    scores, strengths, gaps, and 10/10 model answer.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Find the corresponding question
    matched_q = next((q for q in session.questions if q.id == submission.question_id), None)
    if not matched_q:
        raise HTTPException(status_code=404, detail="Question ID not found in session.")

    retriever = session_store.get_retriever(session_id)
    q_obj = Question(
        question=matched_q.question,
        topic=matched_q.topic,
        difficulty=matched_q.difficulty if matched_q.difficulty in ["easy", "medium", "hard"] else "medium",
    )

    # Score answer using Gemini
    try:
        fb = score_answer(retriever, q_obj, submission.answer_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI Scoring failed: {exc}")

    detailed_fb = DetailedFeedback(
        score=fb.score,
        relevance_score=max(1, min(10, fb.score)),
        technical_correctness_score=max(1, min(10, fb.score)),
        completeness_score=max(1, min(10, fb.score - 1 if fb.gaps else fb.score)),
        communication_clarity_score=max(1, min(10, fb.score)),
        strengths=fb.strengths,
        gaps=fb.gaps,
        technical_corrections=[f"Review: {g}" for g in fb.gaps[:2]],
        improvement_suggestions=fb.gaps,
        model_answer=fb.model_answer,
        recommended_followup_topics=[matched_q.topic],
    )

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    attempt = AnswerAttempt(
        attempt_id=f"att_{uuid.uuid4().hex[:8]}",
        question_id=matched_q.id,
        question_text=matched_q.question,
        topic=matched_q.topic,
        difficulty=matched_q.difficulty,
        answer_text=submission.answer_text,
        audio_filename=submission.audio_filename,
        original_transcript=submission.original_transcript,
        transcript_edited=submission.transcript_edited,
        feedback=detailed_fb,
        created_at=now,
    )

    session.answers.append(attempt)
    if len(session.answers) >= session.config.num_questions:
        session.status = "completed"
        session.overall_score = round(sum(a.feedback.score for a in session.answers) / len(session.answers), 1)

    session_store.save_session(session)
    return attempt


@app.post("/api/v1/interviews/{session_id}/complete", response_model=SessionData, tags=["Interview Sessions"])
def complete_interview(session_id: str):
    """Mark an interview session as completed and calculate aggregate analytics."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    session.status = "completed"
    if session.answers:
        avg = round(sum(a.feedback.score for a in session.answers) / len(session.answers), 1)
        session.overall_score = avg
        session.completion_summary = {
            "average_score": avg,
            "total_completed": len(session.answers),
            "highest_score": max(a.feedback.score for a in session.answers),
            "lowest_score": min(a.feedback.score for a in session.answers),
            "topics_covered": list(set(a.topic for a in session.answers)),
        }
    session_store.save_session(session)
    return session


@app.get("/api/v1/interviews/{session_id}/report", tags=["Interview Sessions"])
def download_interview_report(session_id: str):
    """Generate and download a comprehensive PDF evaluation report."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    pdf_bytes = report_service.generate_pdf_report(session)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="InterviewIQ_Report_{session_id[:8]}.pdf"'},
    )


# ---------------------------------------------------------------------------
# Legacy API Endpoints (Preserved for backward compatibility)
# ---------------------------------------------------------------------------
@app.post("/analyze", response_model=AnalyzeResponse, tags=["Legacy Endpoints"])
def analyze_documents(req: AnalyzeRequest):
    """Legacy endpoint: Ingest JD & Resume, index into ChromaDB, and return skill gap."""
    jd_chunks = []
    resume_chunks = []

    if req.job_text:
        for i, text in enumerate(split_text_by_boundaries(req.job_text)):
            jd_chunks.append(Chunk(id=f"api-jd-{i}", text=text, source="job_description", page=1))
    elif req.use_sample_data and os.path.exists("data/job.txt"):
        jd_chunks = load_document("data/job.txt", "job_description")
    elif req.use_sample_data and os.path.exists("samples/sample_job.txt"):
        jd_chunks = load_document("samples/sample_job.txt", "job_description")

    if req.resume_text:
        for i, text in enumerate(split_text_by_boundaries(req.resume_text)):
            resume_chunks.append(Chunk(id=f"api-res-{i}", text=text, source="resume", page=1))
    elif req.use_sample_data and os.path.exists("data/resume.pdf"):
        resume_chunks = load_document("data/resume.pdf", "resume")
    elif req.use_sample_data and os.path.exists("samples/sample_resume.txt"):
        resume_chunks = load_document("samples/sample_resume.txt", "resume")

    if not jd_chunks or not resume_chunks:
        raise HTTPException(
            status_code=400,
            detail="Both job description and resume must be provided via raw text or bundled sample files.",
        )

    retriever = Retriever()
    retriever.add(jd_chunks + resume_chunks)
    app_state["retriever"] = retriever

    skill_gap = extract_skill_gap(jd_chunks, resume_chunks)

    return AnalyzeResponse(
        status="success",
        skill_gap=skill_gap,
        total_chunks=len(jd_chunks) + len(resume_chunks),
    )


@app.post("/question", response_model=Question, tags=["Legacy Endpoints"])
def get_interview_question(req: QuestionRequest):
    """Legacy endpoint: Generate an interview question targeted at candidate resume and JD."""
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


@app.post("/score", response_model=ScoreResponse, tags=["Legacy Endpoints"])
def score_candidate_answer(req: ScoreRequest):
    """Legacy endpoint: Score a candidate's answer against retrieved ground truth job requirements."""
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
