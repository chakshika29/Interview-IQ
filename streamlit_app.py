import os
import tempfile
import pandas as pd
import streamlit as st

from app.generator import (
    extract_skill_gap,
    generate_adaptive_question,
    generate_question,
    get_next_difficulty,
    score_answer,
)
from app.ingest import load_document
from app.retriever import Retriever

# WHY: Configure the Streamlit page layout and title early so all UI components render in wide mode
st.set_page_config(
    page_title="InterviewIQ - AI Engineer Interview Prep",
    page_icon="🎯",
    layout="wide",
)


def initialize_session_state():
    """
    Initialize persistent state variables across Streamlit rerun cycles.

    WHY: Streamlit re-executes the entire script from top to bottom on every user interaction.
    Storing retriever, skill_gap, questions, feedback, and history in st.session_state ensures
    that data is retained across widget interactions without re-embedding documents.
    """
    if "retriever" not in st.session_state:
        st.session_state.retriever = None
    if "skill_gap" not in st.session_state:
        st.session_state.skill_gap = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "citations" not in st.session_state:
        st.session_state.citations = []
    if "analysis_done" not in st.session_state:
        st.session_state.analysis_done = False
    if "history" not in st.session_state:
        st.session_state.history = []
    if "adaptive_difficulty" not in st.session_state:
        st.session_state.adaptive_difficulty = "medium"


initialize_session_state()


def save_uploaded_file(uploaded_file) -> str:
    """
    Save an uploaded file from Streamlit to a temporary file on disk.

    WHY: pypdf and our ingest functions expect a filesystem path to inspect file headers
    and read document streams safely.
    """
    suffix = os.path.splitext(uploaded_file.name)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


# ---------------------------------------------------------
# Sidebar: Document Management & Interview Settings
# ---------------------------------------------------------
with st.sidebar:
    st.header("📂 Document Setup")
    st.caption("Upload your resume and the target job description to begin.")

    use_defaults = st.checkbox("Use bundled sample data (data/)", value=True)

    resume_path = None
    jd_path = None

    if use_defaults:
        default_resume = "data/resume.pdf"
        default_jd = "data/job.txt"
        if os.path.exists(default_resume) and os.path.exists(default_jd):
            resume_path = default_resume
            jd_path = default_jd
            st.info("Loaded `data/resume.pdf` & `data/job.txt`")
        elif os.path.exists("samples/sample_resume.txt") and os.path.exists("samples/sample_job.txt"):
            resume_path = "samples/sample_resume.txt"
            jd_path = "samples/sample_job.txt"
            st.info("Loaded portfolio sample documents from `samples/`")
        else:
            st.warning("Sample files not found. Please upload documents below.")

    if not use_defaults:
        uploaded_resume = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"])
        uploaded_jd = st.file_uploader("Upload Job Description (PDF or TXT)", type=["pdf", "txt"])

        if uploaded_resume:
            resume_path = save_uploaded_file(uploaded_resume)
        if uploaded_jd:
            jd_path = save_uploaded_file(uploaded_jd)

    # WHY: Allow cloud visitors or reviewers to input their key if not in cloud secrets
    api_key_set = bool(os.getenv("GEMINI_API_KEY") or (hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets))
    if not api_key_set:
        st.divider()
        st.header("🔑 API Key Setup")
        custom_key = st.text_input("Enter GEMINI_API_KEY:", type="password")
        if custom_key:
            os.environ["GEMINI_API_KEY"] = custom_key
            st.success("API key registered for session!")

    st.divider()
    st.header("⚙️ Adaptive Engine")
    st.markdown(
        f"**Current Difficulty Level:** `{st.session_state.adaptive_difficulty.upper()}`\n\n"
        "- Score >= 8: Auto-promotes to harder question.\n"
        "- Score <= 4: Follow-up reinforces the same weak topic at an easier level."
    )

    # WHY: Single 'Analyze' trigger avoids running heavy vector embeddings prematurely
    analyze_clicked = st.button("🚀 Analyze & Build Retriever", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Processing: Ingestion, Vector DB, and Skill Gap
# ---------------------------------------------------------
if analyze_clicked:
    if not resume_path or not jd_path:
        st.error("Please provide both a Resume and a Job Description before analyzing.")
    else:
        with st.spinner("Extracting text chunks and computing Gemini embeddings in ChromaDB..."):
            try:
                # WHY: Load and chunk both documents using sentence boundaries
                jd_chunks = load_document(jd_path, "job_description", chunk_size=600)
                resume_chunks = load_document(resume_path, "resume", chunk_size=600)

                # WHY: Index into ChromaDB vector store + BM25 index
                retriever = Retriever()
                retriever.add(jd_chunks + resume_chunks)

                # WHY: Extract skill gap using Gemini structured output
                skill_gap = extract_skill_gap(jd_chunks, resume_chunks)

                # Save everything in session state
                st.session_state.retriever = retriever
                st.session_state.skill_gap = skill_gap
                st.session_state.analysis_done = True
                st.session_state.current_question = None
                st.session_state.feedback = None
                st.session_state.citations = []
                st.session_state.history = []
                st.session_state.adaptive_difficulty = "medium"

                st.success("Analysis complete! Hybrid index built and skill gap evaluated.")
            except Exception as e:
                st.error(f"Error during analysis: {e}")

# ---------------------------------------------------------
# Main UI Display
# ---------------------------------------------------------
st.title("🎯 InterviewIQ")
st.subheader("Adaptive RAG Technical Interview Simulator for AI Engineers")
st.write(
    "Ground your technical interview preparation in your real resume projects and the exact "
    "expectations of your target job description. The interview loop dynamically adapts "
    "its difficulty and targets your identified knowledge gaps."
)

if st.session_state.analysis_done and st.session_state.skill_gap:
    skill_gap = st.session_state.skill_gap

    # Section 1: Skill Gap Map
    st.header("📊 Skill Gap Map")
    col_chart, col_matched, col_missing = st.columns([1.5, 1.5, 1.5])

    with col_chart:
        chart_df = pd.DataFrame({
            "Category": ["Matched Skills", "Missing / Growth Areas"],
            "Count": [len(skill_gap.matched), len(skill_gap.missing)],
        })
        st.bar_chart(chart_df.set_index("Category"))

    with col_matched:
        st.success(f"**Matched Competencies ({len(skill_gap.matched)})**")
        for skill in skill_gap.matched:
            st.markdown(f"- ✅ {skill}")

    with col_missing:
        st.warning(f"**Areas to Prepare / Missing ({len(skill_gap.missing)})**")
        for skill in skill_gap.missing:
            st.markdown(f"- ⚠️ {skill}")

    st.divider()

    # Section 2: Mock Interview Simulator
    st.header("🎙️ Technical Interview Simulation")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        btn_label = "🎲 Next Question (Adaptive)" if st.session_state.feedback else "🎲 Start First Question"
        if st.button(btn_label, type="primary", use_container_width=True):
            with st.spinner("Formulating grounded question based on current performance..."):
                try:
                    q = generate_adaptive_question(
                        st.session_state.retriever,
                        last_question=st.session_state.current_question,
                        last_feedback=st.session_state.feedback,
                        current_difficulty=st.session_state.adaptive_difficulty,
                    )
                    st.session_state.current_question = q
                    st.session_state.feedback = None
                    st.session_state.citations = []
                    st.session_state.adaptive_difficulty = q.difficulty
                except Exception as e:
                    st.error(f"Error generating question: {e}")

    if st.session_state.current_question:
        q = st.session_state.current_question

        diff_badge = "🟢 Easy" if q.difficulty == "easy" else ("🟡 Medium" if q.difficulty == "medium" else "🔴 Hard")
        st.info(f"**Topic:** {q.topic} &nbsp;|&nbsp; **Difficulty:** {diff_badge}")
        st.markdown(f"### ❓ {q.question}")

        # Form for candidate answer
        with st.form("answer_form"):
            user_answer = st.text_area(
                "Your Answer:",
                height=180,
                placeholder="Walk through your architectural design, implementation details, trade-offs, and tool choices...",
            )
            submit_answer = st.form_submit_button("📝 Score My Answer", type="primary")

        if submit_answer:
            if not user_answer.strip():
                st.warning("Please enter an answer before scoring.")
            else:
                with st.spinner("Scoring answer against retrieved job requirements..."):
                    try:
                        citations = st.session_state.retriever.search(
                            f"{q.topic} {q.question}",
                            k=4,
                            mode="hybrid",
                        )
                        feedback = score_answer(st.session_state.retriever, q, user_answer)

                        st.session_state.feedback = feedback
                        st.session_state.citations = citations

                        # WHY: Record round in history for progress tracking
                        st.session_state.history.append({
                            "round": len(st.session_state.history) + 1,
                            "topic": q.topic,
                            "difficulty": q.difficulty,
                            "score": feedback.score,
                        })

                        # Update next difficulty level
                        next_diff = get_next_difficulty(q.difficulty, feedback.score)
                        st.session_state.adaptive_difficulty = next_diff
                    except Exception as e:
                        st.error(f"Error scoring answer: {e}")

    # Display Feedback
    if st.session_state.feedback:
        fb = st.session_state.feedback
        st.subheader("📋 Evaluation & Feedback")

        # Metric Score Display
        col_score, col_verdict = st.columns([1, 3])
        with col_score:
            st.metric(label="Overall Score", value=f"{fb.score} / 10")
        with col_verdict:
            if fb.score >= 8:
                st.success(
                    f"🌟 **Mastery Demonstrated!** Advancing difficulty to **{st.session_state.adaptive_difficulty.upper()}** for your next question."
                )
            elif fb.score <= 4:
                st.warning(
                    f"⚠️ **Topic Reinforcement Triggered:** Your next question will step down to **{st.session_state.adaptive_difficulty.upper()}** specifically on **{st.session_state.current_question.topic}** to solidify fundamentals."
                )
            else:
                st.info(
                    f"👍 **Solid Progress:** Maintaining difficulty at **{st.session_state.adaptive_difficulty.upper()}**."
                )

        col_str, col_gap = st.columns(2)
        with col_str:
            st.markdown("#### ✅ Strengths")
            for s in fb.strengths:
                st.markdown(f"- {s}")

        with col_gap:
            st.markdown("#### 🔍 Gaps / Missing Points")
            for g in fb.gaps:
                st.markdown(f"- {g}")

        with st.expander("📖 10/10 Model Answer", expanded=True):
            st.markdown(fb.model_answer)

        # Citations section
        if st.session_state.citations:
            with st.expander("📚 Source Chunks Used (RAG Citations)", expanded=False):
                st.caption("These chunks were retrieved from the Job Description and Resume to ground this question and rubric:")
                for i, chunk in enumerate(st.session_state.citations, start=1):
                    source_label = "Job Description" if chunk["source"] == "job_description" else "Resume"
                    st.markdown(f"**Citation {i} [{source_label} - Page {chunk['page']}]:**")
                    st.text(chunk["text"])

    # ---------------------------------------------------------
    # Section 3: Session Score-Progress Chart
    # ---------------------------------------------------------
    if st.session_state.history:
        st.divider()
        st.header("📈 Session Performance & Progress")

        hist_df = pd.DataFrame(st.session_state.history)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Questions Completed", len(hist_df))
        with col_m2:
            avg_score = round(hist_df["score"].mean(), 1)
            st.metric("Average Score", f"{avg_score} / 10")
        with col_m3:
            st.metric("Next Difficulty", st.session_state.adaptive_difficulty.upper())

        # Score line chart over question rounds
        chart_data = hist_df.set_index("round")[["score"]]
        st.line_chart(chart_data)

        with st.expander("📜 View Session Question Log"):
            st.dataframe(hist_df, use_container_width=True)

else:
    st.info("👈 Please click **Analyze & Build Retriever** in the sidebar to load your documents and start your session.")
