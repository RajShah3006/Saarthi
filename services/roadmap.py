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
# services/roadmap.py
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

            programs_for_prompt = [p for p, _, _ in results]

            # LLM analysis only (no steps/program list repetition)
            prompt = self.prompts.roadmap_prompt(profile, programs_for_prompt)
            analysis = self.llm.generate(prompt, self.prompts.roadmap_system_prompt()) or ""

            # UI payload programs
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            # Deterministic phases (no duplication ever)
            phases = self._build_phases(profile, ui_programs)

            # Full plan markdown (deterministic sections)
            full_md = self._format_full_plan(profile, ui_programs, analysis, phases)

            return ServiceResult.success(
                message=full_md,
                data={"programs": ui_programs, "phases": phases, "analysis": analysis},
            )

        except Exception as e:
            logger.error(f"Error: {e}")
            return ServiceResult.failure(str(e))

    def _program_to_payload(self, prog: Program, score: float, bd: Dict[str, Any]) -> Dict[str, Any]:
        def g(obj, attr: str, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        final = bd.get("final", score) if isinstance(bd, dict) else score
        try:
            match_percent = int(round(float(final) * 100))
        except Exception:
            match_percent = 0

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

    def _build_phases(self, profile: StudentProfile, ui_programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        missing = []
        for p in ui_programs:
            for m in (p.get("missing_prereqs") or []):
                m = str(m).strip()
                if m and m not in missing:
                    missing.append(m)

        phases: List[Dict[str, Any]] = []

        if missing:
            phases.append({
                "title": "This month (prerequisites)",
                "items": [f"Register/complete {m}" for m in missing[:6]] + [
                    "Double-check that your top 6 U/M courses match program prerequisites",
                    "Open each program link and confirm the latest requirements",
                ]
            })
        else:
            phases.append({
                "title": "This month (confirm requirements)",
                "items": [
                    "Open your top program links and confirm prerequisites + admission requirements",
                    "Ensure your current course plan covers all required Grade 12 U/M courses",
                ]
            })

        phases.append({
            "title": "Next 2–4 weeks (shortlist)",
            "items": [
                "Shortlist 6–10 programs (mix of safe/target/reach)",
                "Compare prerequisites side-by-side and remove any that don’t match your courses",
                "Keep a tracker: program, prerequisites, admission notes, link",
            ]
        })

        phases.append({
            "title": "Before applications (readiness)",
            "items": [
                "Create a deadline list (OUAC / university-specific items if applicable)",
                "Prepare what you’ll need: grades, activities list, any supplementary forms",
                "Re-check each program page for updates close to application time",
            ]
        })

        return phases[:6]

    def _format_full_plan(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis_md: str,
        phases: List[Dict[str, Any]],
    ) -> str:
        subj = ", ".join(profile.subjects[:5]) if profile.subjects else "Not specified"

        lines: List[str] = []
        lines.append("## ✨ Your Personalized University Roadmap")
        lines.append("")
        lines.append(f"**🎯 Interest:** {profile.interests}  ")
        lines.append(f"**📊 Grade:** {profile.grade} | **Average:** {profile.average}%  ")
        lines.append(f"**📚 Subjects:** {subj}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Top Matching Programs")
        lines.append("")

        for i, p in enumerate(ui_programs[:10], 1):
            name = p.get("program_name", "")
            uni = p.get("university_name", "")
            pct = p.get("match_percent", 0)
            adm = p.get("admission_average") or "Check website"
            pre = p.get("prerequisites") or "Check website"
            miss = p.get("missing_prereqs") or []
            url = p.get("program_url") or ""
            coop = "✅ Co-op Available" if p.get("co_op_available") else ""

            lines.append(f"### {i}. {name}")
            lines.append(f"**{uni}** | 🌟 Match ({pct}%)  ")
            lines.append(f"**Admission (db):** {adm}  ")
            lines.append(f"**Prerequisites (db):** {pre}  ")
            if miss:
                lines.append(f"> ⚠️ **Missing:** {', '.join(miss[:8])}")
            if coop:
                lines.append(coop)
            if url:
                lines.append(f"[View Program Details]({url})")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("## Personalized Analysis")
        lines.append("")
        lines.append(analysis_md.strip() if analysis_md else "- No analysis returned.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Actionable Next Steps")
        lines.append("")
        for ph in phases[:6]:
            title = ph.get("title", "")
            items = ph.get("items", []) or []
            lines.append(f"**{title}:**")
            for it in items[:10]:
                lines.append(f"- {it}")
            lines.append("")

        lines.append("---")
        lines.append("**Tip:** Always verify prerequisites/admission details using the program link (requirements can change).")
        return "\n".join(lines).strip()

    def followup(self, question: str, session: Session) -> ServiceResult:
        try:
            context = session.last_profile.to_context_string() if session.last_profile else ""
            prompt = self.prompts.followup_prompt(question, context)
            response = self.llm.generate(prompt, self.prompts.followup_system_prompt())
            return ServiceResult.success(message=response) if response else ServiceResult.failure("No response")
        except Exception as e:
            return ServiceResult.failure(str(e))
