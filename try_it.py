from app.ingest import load_document
from app.retriever import Retriever
from app.generator import extract_skill_gap, generate_question, score_answer

jd = load_document("data/job.txt", "job_description")
resume = load_document("data/resume.pdf", "resume")

r = Retriever()
r.add(jd + resume)

print("\n--- SKILL GAP ---")
print(extract_skill_gap(jd, resume))

q = generate_question(r, "medium")
print("\n--- QUESTION ---")
print(q.question)

answer = input("\nYour answer: ")
print("\n--- FEEDBACK ---")
print(score_answer(r, q, answer))