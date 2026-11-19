import datetime
import json
import os
import uuid
from typing import Any
from app.retriever import Retriever
from app.schemas import (
    AnswerAttempt,
    InterviewConfig,
    QuestionDetail,
    SessionData,
    SkillGap,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
SESSIONS_DIR = os.path.join(STORAGE_DIR, "sessions")
RECORDINGS_DIR = os.path.join(STORAGE_DIR, "recordings")

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)


class SessionStore:
    """
    Manages session persistence and isolated per-session Hybrid Retrievers.
    Ensures absolute data isolation across different candidates and interviews.
    """

    def __init__(self):
        self._retrievers: dict[str, Retriever] = {}
        self._cache: dict[str, SessionData] = {}

    def get_session_file(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def get_recording_path(self, session_id: str, filename: str) -> str:
        session_rec_dir = os.path.join(RECORDINGS_DIR, session_id)
        os.makedirs(session_rec_dir, exist_ok=True)
        return os.path.join(session_rec_dir, filename)

    def create_session(
        self,
        config: InterviewConfig,
        session_id: str | None = None,
        skill_gap: SkillGap | None = None,
        total_chunks: int = 0,
        resume_preview: dict[str, Any] | None = None,
        jd_preview: dict[str, Any] | None = None,
    ) -> SessionData:
        sid = session_id or str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        session = SessionData(
            id=sid,
            created_at=now,
            updated_at=now,
            status="created",
            config=config,
            skill_gap=skill_gap,
            total_chunks=total_chunks,
            resume_preview=resume_preview,
            jd_preview=jd_preview,
        )
        self.save_session(session)
        return session

    def save_session(self, session: SessionData) -> None:
        session.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._cache[session.id] = session
        filepath = self.get_session_file(session.id)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(session.model_dump_json(indent=2))
        except Exception as e:
            print(f"Warning: Failed to persist session {session.id} to disk: {e}")

    def get_session(self, session_id: str) -> SessionData | None:
        if session_id in self._cache:
            return self._cache[session_id]

        filepath = self.get_session_file(session_id)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session = SessionData.model_validate(data)
                    self._cache[session_id] = session
                    return session
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
                return None
        return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List summary of all persisted sessions ordered by creation date desc."""
        summaries = []
        if not os.path.exists(SESSIONS_DIR):
            return []

        for fname in os.listdir(SESSIONS_DIR):
            if fname.endswith(".json"):
                sid = fname[:-5]
                session = self.get_session(sid)
                if session:
                    avg_score = None
                    if session.answers:
                        avg_score = round(sum(a.feedback.score for a in session.answers) / len(session.answers), 1)

                    summaries.append({
                        "id": session.id,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                        "status": session.status,
                        "interview_type": session.config.interview_type,
                        "difficulty": session.config.difficulty,
                        "total_questions": len(session.questions),
                        "completed_questions": len(session.answers),
                        "average_score": avg_score,
                    })

        summaries.sort(key=lambda s: s["created_at"], reverse=True)
        return summaries

    def get_retriever(self, session_id: str) -> Retriever:
        """Get or create session-isolated retriever instance."""
        if session_id not in self._retrievers:
            self._retrievers[session_id] = Retriever(session_id=session_id)
        return self._retrievers[session_id]

    def set_retriever(self, session_id: str, retriever: Retriever) -> None:
        self._retrievers[session_id] = retriever


session_store = SessionStore()
