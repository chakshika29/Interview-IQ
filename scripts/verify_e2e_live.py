import io
import json
import os
import struct
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def make_request(method: str, path: str, data: dict = None, form_fields: dict = None, files: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = headers or {}
    
    if files or form_fields:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = bytearray()
        if form_fields:
            for field_name, value in form_fields.items():
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'.encode("utf-8"))
                body.extend(str(value).encode("utf-8"))
                body.extend(b"\r\n")
        if files:
            for field_name, (filename, file_bytes, mime) in files.items():
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
                body.extend(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
                body.extend(file_bytes)
                body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        req_data = bytes(body)
    elif data is not None:
        req_headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode("utf-8")
    else:
        req_data = None

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(raw.decode("utf-8"))
            return resp.status, raw
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"error": err_body}

def create_dummy_wav(duration_s=1.0, sample_rate=16000) -> bytes:
    """Create a valid 16kHz mono PCM 16-bit WAV file in-memory."""
    num_samples = int(duration_s * sample_rate)
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align
    
    out = io.BytesIO()
    # RIFF header
    out.write(b"RIFF")
    out.write(struct.pack("<I", 36 + data_size))
    out.write(b"WAVE")
    # fmt chunk
    out.write(b"fmt ")
    out.write(struct.pack("<I", 16)) # Subchunk1Size
    out.write(struct.pack("<H", 1))  # AudioFormat (PCM)
    out.write(struct.pack("<H", num_channels))
    out.write(struct.pack("<I", sample_rate))
    out.write(struct.pack("<I", byte_rate))
    out.write(struct.pack("<H", block_align))
    out.write(struct.pack("<H", bits_per_sample))
    # data chunk
    out.write(b"data")
    out.write(struct.pack("<I", data_size))
    # Low amplitude PCM samples
    out.write(b"\x00" * data_size)
    return out.getvalue()

def run_tests():
    print("=" * 70)
    print("STARTING INTERVIEWIQ PRODUCTION API E2E VERIFICATION")
    print("=" * 70)
    
    # Step 1: Health Check
    print("\n[Step 1] Verifying System Health Endpoint (/api/v1/health)...")
    status, res = make_request("GET", "/api/v1/health")
    assert status == 200, f"Health check failed: {status} {res}"
    print(f"  -> Health OK: status={res.get('status')}, version={res.get('version')}")
    
    # Step 2: AI Health Check (Real Gemini API Call)
    print("\n[Step 2] Testing Real Gemini Connectivity & Health (/api/v1/health/ai?test_call=true)...")
    t0 = time.time()
    status, res = make_request("GET", "/api/v1/health/ai?test_call=true")
    assert status == 200, f"AI Health check failed: {status} {res}"
    elapsed = time.time() - t0
    assert res.get("configured") is True, "Gemini not configured"
    test_call = res.get("test_call", {})
    assert test_call.get("status") == "success", f"Gemini test call failed: {test_call}"
    print(f"  -> Gemini Live Diagnostic SUCCESS ({elapsed:.2f}s):")
    print(f"     Model: {test_call.get('active_model')}")
    print(f"     Status: {test_call.get('status')}")
    print(f"     Latency: {test_call.get('latency_ms')} ms")
    print(f"     Response: '{test_call.get('response')}'")
    
    # Step 3: Resume Upload
    print("\n[Step 3] Testing Resume Upload (multipart/form-data)...")
    sample_resume = (
        "Alex Rivera - Senior AI Engineer\n"
        "Summary: 6 years building production LLM applications, RAG pipelines, and scalable APIs.\n"
        "Skills: Python, FastAPI, LangGraph, ChromaDB, PyTorch, Docker, Kubernetes, AWS, Gemini API, RAG, React.\n"
        "Experience:\n"
        "Lead AI Engineer at DataScale Inc (2022-Present):\n"
        "- Architected enterprise RAG retrieval systems indexing 10M+ documents using hybrid BM25 and vector search.\n"
        "- Integrated Gemini Flash and Claude models for automated data extraction pipelines.\n"
        "- Reduced hallucination rates by 42% using reciprocal rank fusion and semantic chunking.\n"
        "Education: B.S. in Computer Science, UC Berkeley, 2018."
    ).encode("utf-8")
    status, res = make_request("POST", "/api/v1/documents/resume", files={
        "file": ("alex_rivera_resume.txt", sample_resume, "text/plain")
    })
    assert status == 200, f"Resume upload failed: {status} {res}"
    resume_text = res.get("text")
    preview = res.get("preview", {})
    assert resume_text, "No resume text returned"
    print(f"  -> Resume Uploaded Successfully:")
    print(f"     Filename: {res.get('filename')}")
    print(f"     Word count: {preview.get('word_count')}")
    print(f"     Detected sections: {preview.get('detected_sections')}")
    
    # Step 4: Job Description Paste
    print("\n[Step 4] Testing Job Description Paste (raw_text form-data)...")
    sample_jd = (
        "Staff AI Platform Engineer - Core AI Systems\n"
        "Role Overview:\n"
        "We are looking for a Staff AI Engineer to lead the architecture of our next-generation mock interview AI agent.\n"
        "Requirements:\n"
        "- 5+ years of software engineering with deep expertise in Python and FastAPI.\n"
        "- Extensive hands-on experience designing production RAG architectures using ChromaDB or pgvector.\n"
        "- Deep familiarity with Google Gemini SDK, LLM evaluation metrics, and reciprocal rank fusion.\n"
        "- Experience implementing multimodal audio transcription and real-time streaming interfaces.\n"
        "- Strong background in system design, distributed systems, and API reliability."
    )
    status, res = make_request("POST", "/api/v1/documents/job-description", form_fields={"raw_text": sample_jd})
    assert status == 200, f"JD paste failed: {status} {res}"
    job_text = res.get("text")
    jd_preview = res.get("preview", {})
    assert job_text, "No JD text returned"
    print(f"  -> JD Ingested via Paste Successfully:")
    print(f"     Word count: {jd_preview.get('word_count')}")
    print(f"     Detected sections: {jd_preview.get('detected_sections')}")

    # Step 5: Job Description File Upload Option
    print("\n[Step 5] Testing Job Description File Upload Option...")
    jd_file_bytes = sample_jd.encode("utf-8")
    status, res = make_request("POST", "/api/v1/documents/job-description", files={
        "file": ("staff_ai_engineer_jd.txt", jd_file_bytes, "text/plain")
    })
    assert status == 200, f"JD file upload failed: {status} {res}"
    print(f"  -> JD Ingested via File Upload Successfully: filename={res.get('filename')}")

    # Step 6: Create Interview Session (RAG indexing + Gemini Skill Gap Analysis)
    print("\n[Step 6] Creating Interview Session (Triggers RAG vector indexing & Gemini Skill Gap)...")
    t0 = time.time()
    status, session_data = make_request("POST", "/api/v1/interviews", data={
        "resume_text": resume_text,
        "job_text": job_text,
        "config": {
            "interview_type": "technical",
            "difficulty": "adaptive",
            "num_questions": 3,
            "answer_method": "voice_text",
            "time_limit_seconds": 120,
            "enable_followup": True,
            "enable_video": False,
            "enable_detailed_feedback": True
        }
    })
    assert status == 200, f"Interview creation failed: {status} {session_data}"
    session_id = session_data.get("id")
    assert session_id, f"No session id returned: {session_data}"
    elapsed = time.time() - t0
    print(f"  -> Session Created in {elapsed:.2f}s: id={session_id}")
    print(f"  -> RAG Indexed Chunks: {session_data.get('total_chunks')}")
    skill_gap = session_data.get("skill_gap", {})
    print(f"  -> Real Gemini Skill Gap:")
    print(f"     Matched Skills ({len(skill_gap.get('matched', []))}): {skill_gap.get('matched')}")
    print(f"     Missing Skills ({len(skill_gap.get('missing', []))}): {skill_gap.get('missing')}")

    # Step 7: Next Question Generation (Real Gemini + RAG retrieval)
    print("\n[Step 7] Generating Question 1 via Gemini + RAG Context Citations...")
    t0 = time.time()
    status, q_data = make_request("POST", f"/api/v1/interviews/{session_id}/next-question")
    assert status == 200, f"Question generation failed: {status} {q_data}"
    elapsed = time.time() - t0
    q_id = q_data.get("id")
    print(f"  -> Question Generated in {elapsed:.2f}s:")
    print(f"     ID: {q_id}")
    print(f"     Question: \"{q_data.get('question')}\"")
    print(f"     Topic: {q_data.get('topic')} | Difficulty: {q_data.get('difficulty')} | Category: {q_data.get('category')}")
    citations = q_data.get("citations", [])
    print(f"     RAG Grounding Citations: {len(citations)} chunks retrieved from candidate & JD documents")
    for i, c in enumerate(citations[:2]):
        print(f"       [{i+1}] Source: {c.get('source')} | Text: \"{c.get('text', '')[:75]}...\"")

    # Step 8: Audio Transcription (Real Gemini Multimodal Audio STT)
    print("\n[Step 8] Testing Audio Upload & Gemini Multimodal STT Transcription...")
    wav_bytes = create_dummy_wav(duration_s=1.0)
    t0 = time.time()
    status, tr_data = make_request("POST", f"/api/v1/interviews/{session_id}/transcribe", files={
        "file": ("answer_test.wav", wav_bytes, "audio/wav")
    })
    assert status == 200, f"Transcription failed: {status} {tr_data}"
    elapsed = time.time() - t0
    print(f"  -> Gemini Audio STT Completed in {elapsed:.2f}s:")
    print(f"     Transcript: \"{tr_data.get('transcript')}\"")
    print(f"     Audio File Saved: {tr_data.get('audio_filename')}")

    # Step 9: Submit Answer & Evaluate via Gemini Rubric Scoring
    print("\n[Step 9] Submitting Answer for Evaluation (Real Gemini Structured Rubric Scoring)...")
    sample_candidate_answer = (
        "In my previous work at DataScale, I addressed RAG retrieval accuracy and hallucinations by combining "
        "dense vector representations from Gemini embeddings with sparse lexical search using BM25. "
        "We used Reciprocal Rank Fusion with a k constant of 60 to merge the rank lists. "
        "Additionally, we introduced semantic sentence boundary chunking and structured context validation before passing "
        "the retrieved chunks into the prompt, reducing hallucination rates by over 40%."
    )
    t0 = time.time()
    status, eval_data = make_request("POST", f"/api/v1/interviews/{session_id}/answers", data={
        "question_id": q_id,
        "answer_text": sample_candidate_answer,
        "audio_filename": tr_data.get("audio_filename"),
        "original_transcript": tr_data.get("transcript"),
        "transcript_edited": True
    })
    assert status == 200, f"Answer evaluation failed: {status} {eval_data}"
    elapsed = time.time() - t0
    fb = eval_data.get("feedback", {})
    print(f"  -> AI Answer Evaluation Received in {elapsed:.2f}s:")
    print(f"     Overall Score: {fb.get('score')}/10")
    print(f"     Relevance: {fb.get('relevance_score')}/10 | Technical Correctness: {fb.get('technical_correctness_score')}/10")
    print(f"     Completeness: {fb.get('completeness_score')}/10 | Communication Clarity: {fb.get('communication_clarity_score')}/10")
    print(f"     Strengths: {fb.get('strengths')}")
    print(f"     Improvement Areas: {fb.get('gaps')}")
    print(f"     Model Answer Snippet: {fb.get('model_answer', '')[:120]}...")

    # Step 10: Complete Interview Session
    print("\n[Step 10] Completing Interview Session...")
    status, comp_data = make_request("POST", f"/api/v1/interviews/{session_id}/complete")
    assert status == 200, f"Session completion failed: {status} {comp_data}"
    print(f"  -> Session Completed: status={comp_data.get('status')}, overall_score={comp_data.get('overall_score')}/10")
    print(f"  -> Summary: {comp_data.get('completion_summary')}")

    # Step 11: PDF Report Generation
    print("\n[Step 11] Testing Downloadable PDF Report Generation (/report)...")
    status, pdf_bytes = make_request("GET", f"/api/v1/interviews/{session_id}/report")
    assert status == 200, f"PDF report generation failed: {status}"
    assert isinstance(pdf_bytes, bytes), "PDF report returned non-bytes"
    assert pdf_bytes.startswith(b"%PDF"), f"Invalid PDF header: {pdf_bytes[:10]}"
    print(f"  -> PDF Report Successfully Generated: size={len(pdf_bytes):,} bytes, valid %PDF header verified!")

    # Step 12: Verify Session Retrieval & History List
    print("\n[Step 12] Verifying Interview Session Retrieval & History List...")
    status, list_data = make_request("GET", "/api/v1/interviews")
    assert status == 200, f"Session listing failed: {status} {list_data}"
    matching = [s for s in list_data if s.get("id") == session_id]
    assert len(matching) > 0, "Current session not in session list"
    print(f"  -> Session List verified: found {len(list_data)} total saved sessions, current session present!")

    print("\n" + "=" * 70)
    print("ALL API END-TO-END VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return session_id

if __name__ == "__main__":
    sid = run_tests()
    print(f"\nVerification Complete for Session: {sid}")
