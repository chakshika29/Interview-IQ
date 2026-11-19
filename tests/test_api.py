import io
import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import DetailedFeedback, Feedback, Question, SkillGap

client = TestClient(app)


def test_health_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200
    assert r2.json()["version"] == "2.0.0"


def test_ai_health_endpoint():
    r = client.get("/api/v1/health/ai")
    assert r.status_code == 200
    data = r.json()
    assert "configured" in data
    assert "primary_model" in data


def test_document_job_description_paste():
    payload = {"raw_text": "We are seeking a Senior AI Engineer with expertise in Python, FastAPI, and RAG architectures."}
    r = client.post("/api/v1/documents/job-description", data=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "FastAPI" in data["text"]
    assert data["preview"]["word_count"] > 10


def test_document_empty_failure():
    r = client.post("/api/v1/documents/job-description", data={"raw_text": "   "})
    assert r.status_code == 400


def test_upload_resume_txt():
    content = b"Candidate Name: Senior AI Engineer with 5 years of professional experience building LangGraph and FastAPI microservices in cloud environments."
    files = {"file": ("resume.txt", io.BytesIO(content), "text/plain")}
    r = client.post("/api/v1/documents/resume", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "LangGraph" in data["text"]


def test_upload_resume_invalid_ext():
    files = {"file": ("resume.exe", io.BytesIO(b"binary content"), "application/octet-stream")}
    r = client.post("/api/v1/documents/resume", files=files)
    assert r.status_code == 400
    assert "Unsupported file format" in r.json()["detail"]


@patch("app.main.extract_skill_gap")
def test_create_interview_session(mock_gap):
    mock_gap.return_value = SkillGap(
        matched=["Python", "FastAPI"],
        missing=["LangGraph", "ChromaDB"],
    )

    payload = {
        "job_text": "Senior AI Engineer requiring Python, FastAPI, LangGraph, and ChromaDB experience.",
        "resume_text": "Full stack engineer with 4 years building Python and FastAPI microservices.",
        "config": {
            "interview_type": "technical",
            "difficulty": "intermediate",
            "num_questions": 3,
            "answer_method": "voice_text",
        },
    }

    r = client.post("/api/v1/interviews", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    session_id = data["id"]
    assert data["status"] == "created"
    assert data["skill_gap"]["matched"] == ["Python", "FastAPI"]
    assert data["total_chunks"] >= 2

    # Fetch by ID
    r_get = client.get(f"/api/v1/interviews/{session_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == session_id

    # List interviews
    r_list = client.get("/api/v1/interviews")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1


@patch("app.main.generate_question")
@patch("app.main.score_answer")
@patch("app.main.extract_skill_gap")
def test_interview_full_loop(mock_gap, mock_score, mock_q):
    mock_gap.return_value = SkillGap(matched=["Python"], missing=["Docker"])
    mock_q.return_value = Question(
        question="How does asynchronous task concurrency work in Python?",
        topic="Python Concurrency",
        difficulty="medium",
    )
    mock_score.return_value = Feedback(
        score=9,
        strengths=["Clear explanation of asyncio event loop"],
        gaps=["Could mention GIL implications"],
        model_answer="Asyncio operates on a single-threaded cooperative event loop...",
    )

    # 1. Create Session
    create_payload = {
        "job_text": "Backend Engineer proficient in Python asyncio and distributed systems.",
        "resume_text": "Software engineer experienced with Python concurrency and web services.",
        "config": {"num_questions": 1, "difficulty": "adaptive"},
    }
    r_init = client.post("/api/v1/interviews", json=create_payload)
    assert r_init.status_code == 200
    session_id = r_init.json()["id"]

    # 2. Next Question
    r_q = client.post(f"/api/v1/interviews/{session_id}/next-question")
    assert r_q.status_code == 200
    q_data = r_q.json()
    assert q_data["topic"] == "Python Concurrency"
    q_id = q_data["id"]

    # 3. Submit Answer
    ans_payload = {
        "question_id": q_id,
        "answer_text": "Asyncio runs tasks via coroutines yielding control back to the event loop on await expressions.",
    }
    r_ans = client.post(f"/api/v1/interviews/{session_id}/answers", json=ans_payload)
    assert r_ans.status_code == 200
    ans_data = r_ans.json()
    assert ans_data["feedback"]["score"] == 9

    # 4. Complete Session
    r_done = client.post(f"/api/v1/interviews/{session_id}/complete")
    assert r_done.status_code == 200
    assert r_done.json()["status"] == "completed"

    # 5. Download PDF Report
    r_rep = client.get(f"/api/v1/interviews/{session_id}/report")
    assert r_rep.status_code == 200
    assert r_rep.headers["content-type"] == "application/pdf"
    assert len(r_rep.content) > 1000


@patch("app.main.audio_service.transcribe")
@patch("app.main.extract_skill_gap")
def test_transcribe_audio_endpoint(mock_gap, mock_transcribe):
    mock_gap.return_value = SkillGap(matched=["Python"], missing=[])
    mock_transcribe.return_value = "I deployed LangGraph checkpointers with Redis."

    # Create session
    r_init = client.post("/api/v1/interviews", json={
        "job_text": "Python Engineer with LangGraph experience.",
        "resume_text": "Engineer with LangGraph background.",
    })
    session_id = r_init.json()["id"]

    # Fake audio bytes (>100 bytes)
    fake_audio = b"RIFF" + b"\x00" * 200
    files = {"file": ("answer.webm", io.BytesIO(fake_audio), "audio/webm")}
    r_tx = client.post(f"/api/v1/interviews/{session_id}/transcribe", files=files)
    assert r_tx.status_code == 200
    assert r_tx.json()["transcript"] == "I deployed LangGraph checkpointers with Redis."
    assert r_tx.json()["audio_filename"].endswith(".webm")
