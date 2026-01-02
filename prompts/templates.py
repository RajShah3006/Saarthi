# prompts/templates.py - Structured prompt templates
from typing import List
from models import StudentProfile, Program


class PromptTemplates:
    """Centralized prompt templates with clear structure"""
    
    def roadmap_system_prompt(self) -> str:
        return """You are Saarthi AI, a knowledgeable and encouraging university guidance counselor for Canadian high school students.

GUIDELINES:
- Be accurate about admission requirements and prerequisites
- Do NOT fabricate specific statistics, commute times, or costs you don't have data for
- If uncertain, say so and suggest where to find accurate information
- Focus on actionable advice
- Be encouraging but realistic
- Use bullet points and clear formatting"""

    def roadmap_prompt(self, profile: StudentProfile, programs: List[Program]) -> str:
        # Format programs
        programs_text = self._format_programs(programs)
        
        return f"""TASK: Provide personalized university guidance for this student.

STUDENT PROFILE:
{profile.to_context_string()}

MATCHING PROGRAMS (from our database):
{programs_text}

Please provide:

1. **Program Fit Analysis** (2-3 sentences per program)
   - How well does each program match the student's interests?
   - Are there any prerequisite concerns?

2. **Prerequisite Check**
   - Based on the student's subjects, are they on track?
   - What courses should they prioritize?

3. **Extracurricular Alignment**
   - How do their activities support their goals?
   - Suggestions for strengthening their profile?

4. **Actionable Next Steps** (prioritized list)
   - What should they do this semester?
   - What should they do before applications?

5. **Important Considerations**
   - Any concerns or challenges to be aware of?
   - Alternative paths if first choices don't work out?

FORMAT: Use clear headings and bullet points. Be specific and actionable."""

    def followup_system_prompt(self) -> str:
        return """You are Saarthi AI, continuing a conversation about university guidance.

GUIDELINES:
- Reference the previous context when relevant
- Be concise but helpful
- If the question is outside your expertise, say so
- Do not fabricate information"""

    def followup_prompt(self, question: str, context: str) -> str:
        return f"""PREVIOUS CONTEXT:
{context}

STUDENT'S QUESTION:
{question}

Please provide a helpful, specific answer. If you need more information to answer well, ask a clarifying question."""

    def _format_programs(self, programs: List[Program]) -> str:
        if not programs:
            return "No specific programs matched. Provide general guidance."
        
        lines = []
        for i, p in enumerate(programs, 1):
            lines.append(f"{i}. {p.program_name} at {p.university_name}")
            lines.append(f"   Admission: {p.admission_average}")
            lines.append(f"   Prerequisites: {p.prerequisites}")
            if p.co_op_available:
                lines.append(f"   Co-op: Available")
            lines.append("")
        
        return "\n".join(lines)