from typing import Literal
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    id: str
    text: str
    source: Literal["resume", "job_description"]
    page: int | None = None

class Feedback(BaseModel):
    score: int = Field(ge=1, le=10)
    strengths: list[str]
    gaps: list[str]
    model_answer: str

class Question(BaseModel):
    question: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]

class SkillGap(BaseModel):
    matched: list[str]
    missing: list[str]