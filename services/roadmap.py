'''
# services/roadmap.py - Better formatted output
import logging
from typing import List, Tuple, Dict

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")


class RoadmapService:
    def __init__(self, config: Config, llm_client: LLMClient, program_search: ProgramSearchService):
        self.config = config
        self.llm = llm_client
        self.search = program_search
        self.prompts = PromptTemplates()
    
    def generate(self, profile: StudentProfile, session: Session) -> ServiceResult:
        try:
            logger.info(f"Generating for: {profile.interests}")
            
            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            
            if not results:
                return ServiceResult.failure("No programs found.")
            
            programs = [p for p, _, _ in results]
            
            prompt = self.prompts.roadmap_prompt(profile, programs)
            response = self.llm.generate(prompt, self.prompts.roadmap_system_prompt())
            
            if not response:
                return ServiceResult.failure("AI response failed.")
            
            formatted = self._format_output(profile, results, response)
            
            return ServiceResult.success(message=formatted, data={"programs": programs})
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return ServiceResult.failure(str(e))
    
    def _format_output(self, profile: StudentProfile, results: List[Tuple], ai_response: str) -> str:
        """Beautiful formatted output"""
        
        # Header
        output = f"""
<div class="roadmap-header">

## ✨ Your Personalized University Roadmap

**🎯 Interest:** {profile.interests}  
**📊 Grade:** {profile.grade} | **Average:** {profile.average}%  
**📚 Subjects:** {', '.join(profile.subjects[:5]) if profile.subjects else 'Not specified'}

</div>

---

## 🎓 Top Matching Programs

"""
        
        for i, (prog, score, bd) in enumerate(results, 1):
            # Match quality
            if bd['final'] >= 0.7:
                match_class = "excellent"
                match_icon = "🌟"
                match_text = "Excellent Match"
            elif bd['final'] >= 0.5:
                match_class = "good"
                match_icon = "✅"
                match_text = "Good Match"
            elif bd['final'] >= 0.3:
                match_class = "moderate"
                match_icon = "🔶"
                match_text = "Moderate Match"
            else:
                match_class = "low"
                match_icon = "⚪"
                match_text = "Low Match"
            
            # Grade assessment styling
            grade_assessment = bd.get('grade_assessment', 'Unknown')
            if grade_assessment == "Safe":
                grade_icon = "🟢"
            elif grade_assessment == "Good":
                grade_icon = "🟢"
            elif grade_assessment == "Target":
                grade_icon = "🟡"
            elif grade_assessment == "Reach":
                grade_icon = "🟠"
            else:
                grade_icon = "🔴"
            
            # Missing prerequisites
            missing = bd.get('missing_prereqs', [])
            prereq_warning = ""
            if missing:
                prereq_warning = f"\n> ⚠️ **Missing:** {', '.join(missing)}"
            
            # Clean prerequisites display
            prereqs_display = prog.prerequisites[:150] + "..." if len(prog.prerequisites) > 150 else prog.prerequisites
            if not prereqs_display:
                prereqs_display = "Check university website"
            
            output += f"""
### {i}. {prog.program_name}

**{prog.university_name}** | {match_icon} **{match_text}** ({bd['final']:.0%})

| Metric | Score | Details |
|--------|-------|---------|
| 🎯 Relevance | {bd['relevance']:.0%} | How well it matches your interests |
| 📊 Grade Fit | {grade_icon} {bd['grade']:.0%} | {grade_assessment} |
| 📋 Prerequisites | {bd['prereq']:.0%} | Course requirements met |
| 📍 Location | {bd['location'] if isinstance(bd['location'], str) else f"{bd['location']:.0%}"} | Distance preference |

**📝 Admission:** {prog.admission_average or 'Check website'}  
**📚 Prerequisites:** {prereqs_display}{prereq_warning}

{"✅ **Co-op Available**" if prog.co_op_available else ""}

🔗 [View Program Details]({prog.program_url})

---

"""
        
        # AI Analysis
        output += f"""
## 🤖 Personalized Analysis

{ai_response}

---

<div class="footer-note">

💡 **Tip:** Click on program links for the most up-to-date admission requirements.  
❓ **Questions?** Ask below for more details about any program!

</div>
"""
        
        return output
    
    def followup(self, question: str, session: Session) -> ServiceResult:
        try:
            context = session.last_profile.to_context_string() if session.last_profile else ""
            prompt = self.prompts.followup_prompt(question, context)
            response = self.llm.generate(prompt, self.prompts.followup_system_prompt())
            return ServiceResult.success(message=response) if response else ServiceResult.failure("No response")
        except Exception as e:
            return ServiceResult.failure(str(e))
'''
# services/roadmap.py - Better formatted output + UI-safe structured program payload

import logging
from typing import List, Tuple, Dict, Any

from config import Config
from models import StudentProfile, Session, ServiceResult, Program

from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")


class RoadmapService:
    def __init__(self, config: Config, llm_client: LLMClient, program_search: ProgramSearchService):
        self.config = config
        self.llm = llm_client
        self.search = program_search
        self.prompts = PromptTemplates()

    def generate(self, profile: StudentProfile, session: Session) -> ServiceResult:
        try:
            logger.info(f"Generating for: {profile.interests}")

            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            if not results:
                return ServiceResult.failure("No programs found.")

            # Used for the LLM prompt (can be Program objects)
            programs_for_prompt = [p for p, _, _ in results]

            prompt = self.prompts.roadmap_prompt(profile, programs_for_prompt)
            response = self.llm.generate(prompt, self.prompts.roadmap_system_prompt())
            if not response:
                return ServiceResult.failure("AI response failed.")

            formatted = self._format_output(profile, results, response)

            # ✅ UI-safe payload (dicts only, small, includes match + prereq info)
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            return ServiceResult.success(message=formatted, data={"programs": ui_programs})

        except Exception as e:
            logger.error(f"Error: {e}")
            return ServiceResult.failure(str(e))

    def _program_to_payload(self, prog: Program, score: float, bd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Program object (or dict-like) + breakdown into a compact dict for UI embedding.
        Avoid embeddings/large fields.
        """
        # Support both Program objects and dicts defensively
        def g(obj, attr: str, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        final = bd.get("final", score) if isinstance(bd, dict) else score
        try:
            match_percent = int(round(float(final) * 100))
        except Exception:
            match_percent = None

        payload = {
            "program_name": g(prog, "program_name", "") or "",
            "university_name": g(prog, "university_name", "") or g(prog, "university", "") or "",
            "program_url": g(prog, "program_url", "") or g(prog, "url", "") or "",
            "admission_average": g(prog, "admission_average", "") or "",
            "prerequisites": g(prog, "prerequisites", "") or "",
            "co_op_available": bool(g(prog, "co_op_available", False) or g(prog, "coop_available", False)),
            "match_percent": match_percent,
            "missing_prereqs": bd.get("missing_prereqs", []) if isinstance(bd, dict) else [],
            "grade_assessment": bd.get("grade_assessment") if isinstance(bd, dict) else None,
            "metrics": {
                "final": bd.get("final") if isinstance(bd, dict) else None,
                "relevance": bd.get("relevance") if isinstance(bd, dict) else None,
                "grade": bd.get("grade") if isinstance(bd, dict) else None,
                "prereq": bd.get("prereq") if isinstance(bd, dict) else None,
                "location": bd.get("location") if isinstance(bd, dict) else None,
            },
        }
        return payload

    def _format_output(self, profile: StudentProfile, results: List[Tuple], ai_response: str) -> str:
        """Beautiful formatted output"""

        output = f"""
## ✨ Your Personalized University Roadmap
🎯 Interest: {profile.interests}
📊 Grade: {profile.grade} | Average: {profile.average}%
📚 Subjects: {', '.join(profile.subjects[:5]) if profile.subjects else 'Not specified'}
---
## Top Matching Programs
"""

        for i, (prog, score, bd) in enumerate(results, 1):
            if bd["final"] >= 0.7:
                match_icon = "🌟"
                match_text = "Excellent Match"
            elif bd["final"] >= 0.5:
                match_icon = "✅"
                match_text = "Good Match"
            elif bd["final"] >= 0.3:
                match_icon = "🟡"
                match_text = "Moderate Match"
            else:
                match_icon = "⚪"
                match_text = "Low Match"

            grade_assessment = bd.get("grade_assessment", "Unknown")

            missing = bd.get("missing_prereqs", [])
            prereq_warning = f"\n> ⚠️ **Missing:** {', '.join(missing)}" if missing else ""

            prereqs_display = (prog.prerequisites or "").strip()
            if prereqs_display:
                prereqs_display = prereqs_display[:150] + ("..." if len(prereqs_display) > 150 else "")
            else:
                prereqs_display = "Check university website"

            match_percent = int(round(bd["final"] * 100))
            admission = prog.admission_average or "Check website"
            
            missing = bd.get("missing_prereqs", [])
            missing_line = f"⚠️ Missing: {', '.join(missing)}" if missing else ""
            
            prereqs_display = (prog.prerequisites or "").strip()
            if prereqs_display:
                prereqs_display = prereqs_display[:150] + ("..." if len(prereqs_display) > 150 else "")
            else:
                prereqs_display = "Check university website"
            
            coop_line = "✅ Co-op Available" if prog.co_op_available else ""
            
            output += f"""
{i}. {prog.program_name}
{prog.university_name} | {match_icon} {match_text} ({match_percent}%)
📝 Admission: {admission}
📚 Prerequisites: {prereqs_display}
{missing_line}
{coop_line}
🔗 Link: {prog.program_url}
---
"""

        output += f"""
## Personalized Analysis
{ai_response}

---

<div class="footer-note">

**Tip:** Click on program links for the most up-to-date admission requirements.  
❓ **Questions?** Ask below for more details about any program!

</div>
"""
        return output

    def followup(self, question: str, session: Session) -> ServiceResult:
        try:
            context = session.last_profile.to_context_string() if session.last_profile else ""
            prompt = self.prompts.followup_prompt(question, context)
            response = self.llm.generate(prompt, self.prompts.followup_system_prompt())
            return ServiceResult.success(message=response) if response else ServiceResult.failure("No response")
        except Exception as e:
            return ServiceResult.failure(str(e))