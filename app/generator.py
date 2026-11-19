import os
from typing import Any
from dotenv import load_dotenv
from google import genai

from app.schemas import Feedback, Question, SkillGap
from app.services.gemini_service import gemini_service

# Load environment variables
load_dotenv()

# Configured model for backward compatibility
MODEL_NAME = gemini_service.primary_model


def get_client() -> genai.Client:
    """
    Get or initialize the Google GenAI client via gemini_service.
    Retained for backward compatibility with existing tests and scripts.
    """
    return gemini_service.get_client()


def generate_with_retry(
    client_instance: Any,
    model: str,
    contents: str,
    schema: type,
    max_retries: int = 4,
    initial_delay: float = 1.5,
):
    """
    Structured generation delegate routed through resilient GeminiService.
    """
    return gemini_service.generate_structured(
        prompt=contents,
        schema=schema,
        max_retries_per_model=max_retries,
        initial_delay=initial_delay,
    )


def extract_skill_gap(jd_chunks, resume_chunks) -> SkillGap:
    """
    Compare job description requirements against resume to identify matched and missing skills.
    """
    jd_text = "\n\n".join(c.text if hasattr(c, "text") else str(c) for c in jd_chunks)
    resume_text = "\n\n".join(c.text if hasattr(c, "text") else str(c) for c in resume_chunks)

    prompt = f"""You are an expert AI Engineer hiring manager and technical interviewer.
Analyze the provided Job Description and the Candidate's Resume below.

Extract and categorize technical skills, tools, methodologies, and architectural concepts:
- "matched": Skills, technologies, and competencies that are required/preferred by the job AND clearly demonstrated in the candidate's resume.
- "missing": Core skills, frameworks, or qualifications required or strongly desired by the job that are absent, weak, or insufficiently demonstrated in the resume.

JOB DESCRIPTION:
{jd_text}

CANDIDATE RESUME:
{resume_text}
"""
    return gemini_service.generate_structured(prompt, SkillGap)


def generate_question(retriever, difficulty: str = "medium") -> Question:
    """
    Generate an interview question targeted at specific skills/projects in candidate's resume
    that intersect with the target job description.
    """
    resume_docs = retriever.search("technical projects tools architecture hands-on experience", k=3, source="resume")
    jd_docs = retriever.search("core requirements responsibilities qualifications skills", k=3, source="job_description")

    resume_context = "\n---\n".join(d["text"] for d in resume_docs)
    jd_context = "\n---\n".join(d["text"] for d in jd_docs)

    prompt = f"""You are an elite technical interviewer conducting a mock interview for an AI Engineer position.
Target Difficulty: {difficulty}

Relevant details from the candidate's resume:
{resume_context}

Relevant requirements from the job description:
{jd_context}

Task:
Generate a single, insightful interview question at the '{difficulty}' level.
Requirements:
1. Strongly prefer asking about a specific tool, framework, or project mentioned in the candidate's resume that intersects with the job requirements (e.g. LangGraph, RAG pipelines, FastAPI backend engineering, agent state management).
2. The question should evaluate both practical implementation decisions and theoretical understanding.
3. Identify the main technical topic.
4. Set difficulty strictly to '{difficulty}'.
"""
    return gemini_service.generate_structured(prompt, Question)


def get_next_difficulty(current_difficulty: str, last_score: int) -> str:
    """
    Determine next question difficulty based on candidate's score:
    - Score >= 8: Advances difficulty (easy -> medium -> hard).
    - Score <= 4: Drops difficulty (hard -> medium -> easy) to reinforce weak topics.
    - Score 5-7: Keeps current difficulty for balanced progression.
    """
    levels = ["easy", "medium", "hard"]
    idx = levels.index(current_difficulty.lower()) if current_difficulty.lower() in levels else 1

    if last_score >= 8:
        return levels[min(idx + 1, 2)]
    if last_score <= 4:
        return levels[max(idx - 1, 0)]
    return levels[idx]


def generate_adaptive_question(
    retriever,
    last_question: Question | None = None,
    last_feedback: Feedback | None = None,
    current_difficulty: str = "medium",
) -> Question:
    """
    Generate the next question adaptively based on previous score and identified weaknesses.
    """
    if last_feedback is not None:
        next_difficulty = get_next_difficulty(current_difficulty, last_feedback.score)
    else:
        next_difficulty = current_difficulty

    # Case A: Low score (<= 4) -> Drill down on the SAME weak topic with an easier question
    if last_feedback is not None and last_feedback.score <= 4 and last_question is not None:
        target_topic = last_question.topic
        gaps_summary = "; ".join(last_feedback.gaps) if last_feedback.gaps else "fundamental concepts"

        jd_docs = retriever.search(target_topic, k=2, source="job_description")
        resume_docs = retriever.search(target_topic, k=2, source="resume")
        jd_context = "\n---\n".join(d["text"] for d in jd_docs)
        resume_context = "\n---\n".join(d["text"] for d in resume_docs)

        prompt = f"""You are a supportive technical interviewer conducting an adaptive interview.
The candidate struggled on the previous question regarding "{target_topic}" (Score: {last_feedback.score}/10).
Identified Gaps: {gaps_summary}

Relevant Context:
{jd_context}
{resume_context}

Task:
Generate an easier, foundational follow-up question on "{target_topic}" at the '{next_difficulty}' level.
Goal: Help the candidate demonstrate their foundational understanding of this topic before moving on to advanced architecture.
Identify the topic as "{target_topic}" and set difficulty strictly to '{next_difficulty}'.
"""
        return gemini_service.generate_structured(prompt, Question)

    # Case B: High score (>= 8) -> Challenge with harder difficulty
    if last_feedback is not None and last_feedback.score >= 8 and last_question is not None:
        resume_docs = retriever.search("technical projects tools architecture hands-on experience", k=3, source="resume")
        jd_docs = retriever.search("core requirements responsibilities qualifications skills", k=3, source="job_description")
        resume_context = "\n---\n".join(d["text"] for d in resume_docs)
        jd_context = "\n---\n".join(d["text"] for d in jd_docs)

        prompt = f"""You are a principal engineer conducting an elite technical interview.
The candidate demonstrated strong mastery on the previous question (Score: {last_feedback.score}/10).

Target Difficulty: {next_difficulty} (Hard / Advanced)

Candidate Projects:
{resume_context}

Job Requirements:
{jd_context}

Task:
Generate a challenging, advanced interview question at '{next_difficulty}' level.
Focus on complex edge cases, distributed failure modes, concurrency, latency trade-offs, or production architectural design
intersecting the candidate's resume projects and the job requirements.
Identify the technical topic and set difficulty strictly to '{next_difficulty}'.
"""
        return gemini_service.generate_structured(prompt, Question)

    # Case C: First question or moderate score (5-7) -> Standard grounded question
    return generate_question(retriever, difficulty=next_difficulty)


def score_answer(retriever, question, answer: str) -> Feedback:
    """
    Evaluate a candidate's answer against the target job requirements using RAG context.
    """
    q_text = question.question if isinstance(question, Question) else str(question)
    q_topic = question.topic if isinstance(question, Question) else ""

    jd_docs = retriever.search(f"{q_topic} {q_text}", k=3, source="job_description")
    jd_context = "\n---\n".join(d["text"] for d in jd_docs)

    prompt = f"""You are a senior AI Engineering manager scoring a candidate's interview answer.

Question: {q_text}
Topic: {q_topic}

Candidate's Answer:
{answer}

Ground Truth Job Requirements:
{jd_context}

Evaluation Instructions:
1. Score the answer from 1 to 10 (1 = completely incorrect or irrelevant, 10 = production-grade, comprehensive master-level answer).
2. List specific strengths (accurate points, solid design intuition, good technical details).
3. List specific gaps (missing edge cases, production concerns, architectural trade-offs, or requirements from the job not met).
4. Provide a clear, polished model answer that demonstrates what a 10/10 response looks like for this AI Engineer role.
"""
    feedback = gemini_service.generate_structured(prompt, Feedback)
    feedback.score = max(1, min(10, feedback.score))
    return feedback


def answer_query_with_guardrail(retriever, query: str) -> str:
    """
    Answer an informational question strictly based on retrieved documents, with a guardrail
    that returns 'Information not found in the documents.' if retrieval is weak.
    """
    docs = retriever.search(query, k=3, mode="hybrid")
    if retriever.is_retrieval_weak(docs):
        return "Information not found in the documents."

    context = "\n---\n".join(d["text"] for d in docs)
    prompt = f"""You are a strictly grounded question answering assistant.
Answer the user's question using ONLY the facts explicitly stated in the Context below.
If the context does not provide sufficient information to answer the question, respond with:
"Information not found in the documents."
Do not make up facts or extrapolate beyond the context.

Context:
{context}

Question:
{query}
"""
    return gemini_service.generate_text(prompt)
