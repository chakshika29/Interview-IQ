import pytest
from pydantic import ValidationError
from app.schemas import Chunk, Feedback, Question, SkillGap


def test_chunk_creation():
    """Verify Chunk data model instantiation and attribute access."""
    chunk = Chunk(
        id="resume-1-0",
        text="Experience with Python and FastAPI",
        source="resume",
        page=1,
    )
    assert chunk.id == "resume-1-0"
    assert chunk.source == "resume"
    assert chunk.page == 1
    assert "FastAPI" in chunk.text


def test_feedback_valid_score():
    """Verify Feedback model accepts scores within the 1-10 boundary."""
    fb = Feedback(
        score=8,
        strengths=["Clear architectural explanation"],
        gaps=["Did not cover failure scenarios"],
        model_answer="A production answer includes error handling...",
    )
    assert fb.score == 8
    assert len(fb.strengths) == 1
    assert len(fb.gaps) == 1


def test_feedback_score_validation_bounds():
    """Verify Feedback model rejects scores below 1 or above 10."""
    with pytest.raises(ValidationError):
        Feedback(
            score=0,  # Below lower bound
            strengths=[],
            gaps=[],
            model_answer="",
        )

    with pytest.raises(ValidationError):
        Feedback(
            score=11,  # Above upper bound
            strengths=[],
            gaps=[],
            model_answer="",
        )


def test_question_model():
    """Verify Question schema fields and difficulty constraints."""
    q = Question(
        question="How do checkpointers persist state in LangGraph?",
        topic="LangGraph State Management",
        difficulty="medium",
    )
    assert q.difficulty == "medium"
    assert q.topic == "LangGraph State Management"

    # Difficulty must match Literal['easy', 'medium', 'hard']
    with pytest.raises(ValidationError):
        Question(
            question="What is RAG?",
            topic="RAG",
            difficulty="extreme",  # Invalid difficulty
        )


def test_skill_gap_model():
    """Verify SkillGap categorization into matched and missing lists."""
    gap = SkillGap(
        matched=["Python", "FastAPI", "Docker"],
        missing=["LangGraph", "Copilot Studio"],
    )
    assert "Python" in gap.matched
    assert "Copilot Studio" in gap.missing
