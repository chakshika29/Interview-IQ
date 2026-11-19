import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.schemas import SessionData


class ReportService:
    """
    Generates professional PDF interview performance reports using ReportLab.
    """

    def generate_pdf_report(self, session: SessionData) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e1b4b"),
            alignment=0,
            fontName="Helvetica-Bold",
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#4b5563"),
        )

        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#4338ca"),
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )

        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1f2937"),
        )

        bold_label = ParagraphStyle(
            "BoldLabel",
            parent=body_style,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#111827"),
        )

        story = []

        # Header Title
        story.append(Paragraph("🎯 InterviewIQ Evaluation Report", title_style))
        story.append(Paragraph("AI-Grounded Technical Mock Interview Analysis", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=12))

        # Metadata Table
        avg_score = (
            round(sum(a.feedback.score for a in session.answers) / len(session.answers), 1)
            if session.answers
            else 0.0
        )

        meta_data = [
            [
                Paragraph("<b>Session ID:</b>", body_style),
                Paragraph(session.id[:18] + "...", body_style),
                Paragraph("<b>Date:</b>", body_style),
                Paragraph(session.created_at[:10], body_style),
            ],
            [
                Paragraph("<b>Interview Type:</b>", body_style),
                Paragraph(session.config.interview_type.capitalize(), body_style),
                Paragraph("<b>Difficulty:</b>", body_style),
                Paragraph(session.config.difficulty.capitalize(), body_style),
            ],
            [
                Paragraph("<b>Questions Answered:</b>", body_style),
                Paragraph(f"{len(session.answers)} / {len(session.questions)}", body_style),
                Paragraph("<b>Overall Score:</b>", bold_label),
                Paragraph(f"<b>{avg_score} / 10</b>", bold_label),
            ],
        ]

        t_meta = Table(meta_data, colWidths=[110, 150, 110, 160])
        t_meta.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(t_meta)
        story.append(Spacer(1, 14))

        # Skill Gap Summary
        if session.skill_gap:
            story.append(Paragraph("📊 Skill Gap Analysis", h2_style))
            matched_text = ", ".join(session.skill_gap.matched) if session.skill_gap.matched else "None specified"
            missing_text = ", ".join(session.skill_gap.missing) if session.skill_gap.missing else "None identified"

            gap_data = [
                [Paragraph("<b>✅ Matched Competencies:</b>", bold_label), Paragraph(matched_text, body_style)],
                [Paragraph("<b>⚠️ Focus / Growth Areas:</b>", bold_label), Paragraph(missing_text, body_style)],
            ]
            t_gap = Table(gap_data, colWidths=[150, 380])
            t_gap.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(t_gap)
            story.append(Spacer(1, 14))

        # Question by Question Breakdown
        story.append(Paragraph("📝 Question Evaluation & Feedback", h2_style))

        if not session.answers:
            story.append(Paragraph("<i>No questions were completed during this session.</i>", body_style))
        else:
            for idx, ans in enumerate(session.answers, start=1):
                fb = ans.feedback
                q_box = [
                    [
                        Paragraph(f"<b>Round {idx}: {ans.topic}</b> ({ans.difficulty.upper()})", bold_label),
                        Paragraph(f"<b>Score: {fb.score} / 10</b>", bold_label),
                    ],
                    [
                        Paragraph(f"<b>Question:</b> {ans.question_text}", body_style),
                        Paragraph("", body_style),
                    ],
                    [
                        Paragraph(f"<b>Candidate Answer:</b> {ans.answer_text}", body_style),
                        Paragraph("", body_style),
                    ],
                ]

                # Strengths
                str_items = "<br/>• ".join(fb.strengths) if fb.strengths else "Good foundational effort."
                q_box.append([
                    Paragraph("<b>✅ Strengths:</b><br/>• " + str_items, body_style),
                    Paragraph("", body_style),
                ])

                # Gaps
                gap_items = "<br/>• ".join(fb.gaps) if fb.gaps else "No major architectural gaps noted."
                q_box.append([
                    Paragraph("<b>🔍 Gaps:</b><br/>• " + gap_items, body_style),
                    Paragraph("", body_style),
                ])

                # Model Answer
                if fb.model_answer:
                    q_box.append([
                        Paragraph(f"<b>💡 10/10 Model Answer:</b><br/>{fb.model_answer[:450]}...", body_style),
                        Paragraph("", body_style),
                    ])

                t_q = Table(q_box, colWidths=[420, 110])
                t_q.setStyle(
                    TableStyle([
                        ("SPAN", (0, 1), (1, 1)),
                        ("SPAN", (0, 2), (1, 2)),
                        ("SPAN", (0, 3), (1, 3)),
                        ("SPAN", (0, 4), (1, 4)),
                        ("SPAN", (0, 5), (1, 5)) if len(q_box) > 5 else ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#a5b4fc")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ])
                )
                story.append(t_q)
                story.append(Spacer(1, 10))

        doc.build(story)
        return buffer.getvalue()


report_service = ReportService()
