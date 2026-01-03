# prompts/templates.py - LLM prompt templates

from typing import List
from models import StudentProfile, Program


class PromptTemplates:
    def roadmap_system_prompt(self) -> str:
        return """You are Saarthi AI, a knowledgeable and encouraging university guidance counselor for Ontario high school students.

You help Ontario students choose university programs and create actionable roadmaps.

GUIDELINES:
- Be accurate about admission requirements and prerequisites.
- Do NOT fabricate specific statistics, commute times, or costs you don't have data for.
- If uncertain, say so and suggest where to find accurate information.
- Focus on actionable advice.
- Be encouraging but realistic.
- Use bullet points and clear formatting.
- Do NOT include a "Budget considerations" section unless the student explicitly asks about tuition, cost, or financial aid.
- If the student mentions scholarships/aid, give high-level actions (where to check, how to prepare) rather than making up numbers.
"""

    def roadmap_prompt(self, profile: StudentProfile, programs: List[Program]) -> str:
        programs_text = self._format_programs_list(programs)

        return f"""STUDENT PROFILE:
{profile.to_context_string()}

MATCHING PROGRAMS (from our database):
{programs_text}

NOTE: If the student provided preferences/constraints (e.g., co-op, commuting, scholarships, campus vibe, program size),
weave them into the recommendations and next steps. Avoid making up costs.

TASK: Create a personalized roadmap with:
1. Summary of why these programs match the student
2. Top 3 program recommendations with reasons
3. Grade 12 course plan (what to focus on)
4. Extracurricular/portfolio suggestions relevant to their interests
5. Application tips and deadlines (general Ontario guidance)
6. Next steps checklist

FORMAT: Use clear headings and bullet points. Be specific and actionable.
"""

    def followup_system_prompt(self) -> str:
        return """You are Saarthi AI. Answer student questions about Ontario university programs.
Be accurate and helpful. If you don't know something, say so and suggest where to verify."""

    def followup_prompt(self, question: str, context: str) -> str:
        return f"""CONTEXT:
{context}

QUESTION:
{question}

Answer clearly and helpfully. If the question needs program-specific details, suggest checking the official program page."""
    
    def _format_programs_list(self, programs: List[Program], max_programs: int = 10) -> str:
        formatted = []
        for i, program in enumerate(programs[:max_programs], 1):
            formatted.append(
                f"{i}. {program.program_name} at {program.university_name}\n"
                f"   - Admission Average: {program.admission_average}\n"
                f"   - Prerequisites: {program.prerequisites}\n"
                f"   - Co-op: {'Yes' if program.co_op_available else 'No'}\n"
            )
        return "\n".join(formatted)
