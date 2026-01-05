# prompts/templates.py
from typing import List
from models import StudentProfile, Program


class PromptTemplates:
    """Centralized prompt templates with clear structure"""

    def roadmap_system_prompt(self) -> str:
        return """You are Saarthi AI, a helpful Canadian university guidance counselor.
RULES:
- Use ONLY the provided database program info for prerequisites/admission fields (do not invent numbers).
- If something seems uncertain or outdated, say: "Verify on the program link" (do not guess).
- Focus on university planning only (program fit, prerequisites, application readiness).
- Do NOT repeat a full program list or produce an "Actionable Next Steps" section (the app generates those).
- Output should be concise and useful: 6–12 bullet points max, grouped by short headings.
"""

    def roadmap_prompt(self, profile: StudentProfile, programs: List[Program]) -> str:
        programs_text = self._format_programs(programs)

        return f"""STUDENT PROFILE:
{profile.to_context_string()}

MATCHING PROGRAMS (database snapshot):
{programs_text}

TASK:
Write a short "Personalized Analysis" ONLY.
Include:
- Best-fit themes (why these programs match interests)
- Prerequisite/subject risks (based on student subjects)
- Admission-data caution (if needed) + "verify on link"
- How to shortlist programs intelligently

FORMAT:
Use 2–4 mini headings with bullets. Do not list all programs again. Do not write a checklist.
"""

    def followup_system_prompt(self) -> str:
        return """You are Saarthi AI, continuing a conversation about Canadian university guidance.
RULES:
- Be direct and specific.
- If you do not know something, say so and point to what to check.
- Do not fabricate facts or statistics.
"""

    def followup_prompt(self, question: str, context: str) -> str:
        return f"""CONTEXT:
{context}

QUESTION:
{question}

Answer clearly in 6–10 bullets or a short structured response.
"""

    def _format_programs(self, programs: List[Program]) -> str:
        if not programs:
            return "No specific programs matched."

        lines = []
        for i, p in enumerate(programs, 1):
            lines.append(f"{i}. {p.program_name} at {p.university_name}")
            lines.append(f"   Admission (db): {p.admission_average}")
            lines.append(f"   Prerequisites (db): {p.prerequisites}")
            lines.append(f"   Link: {p.program_url}")
            lines.append("")
        return "\n".join(lines)
