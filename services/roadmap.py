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
import re
from datetime import date, datetime
from typing import List, Tuple, Dict, Any

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")

COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3}\d[A-Za-z])\b")  # e.g., MHF4U, SCH4U, etc. (case-insensitive)

def _today_iso() -> str:
    return date.today().isoformat()

def _parse_ouac_deadline() -> date:
    """
    Equal consideration is typically Jan 15.
    For current cycle (today <= Jan 15), use this year's Jan 15.
    If today passed, use next year's Jan 15.
    """
    today = date.today()
    yr = today.year
    dl = date(yr, 1, 15)
    if today > dl:
        dl = date(yr + 1, 1, 15)
    return dl

def _iso(d: date) -> str:
    return d.isoformat()

def _clean_course_codes(text: str) -> List[str]:
    if not text:
        return []
    hits = [m.group(1).upper() for m in COURSE_CODE_RE.finditer(text)]
    # normalize last letter to U/M (sometimes weird cases)
    out = []
    seen = set()
    for h in hits:
        h = h.replace("O", "0")
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:12]

def _clean_prereq_display(text: str) -> str:
    # Prefer showing just course codes if they exist
    codes = _clean_course_codes(text or "")
    if codes:
        return ", ".join(codes)
    # fallback: compact the string
    s = re.sub(r"\s+", " ", (text or "")).strip()
    s = re.sub(r",\s*,+", ", ", s).strip(" ,")
    return s[:180] + ("…" if len(s) > 180 else "")

class RoadmapService:
    def __init__(self, config: Config, llm_client: LLMClient, program_search: ProgramSearchService):
        self.config = config
        self.llm = llm_client
        self.search = program_search
        self.prompts = PromptTemplates()

    def generate(self, profile: StudentProfile, session: Session) -> ServiceResult:
        try:
            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            if not results:
                return ServiceResult.failure("No programs found.")

            programs_for_prompt = [p for p, _, _ in results]

            # 1) AI ANALYSIS (content)
            prompt = self.prompts.roadmap_prompt(profile, programs_for_prompt)
            analysis = (self.llm.generate(prompt, self.prompts.roadmap_system_prompt()) or "").strip()

            # 2) UI programs (cleaned fields)
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            # 3) Unique timeline + unique checklist projects
            timeline_events = self._build_timeline(profile)
            projects = self._build_projects(profile)

            # 4) Full plan: ask AI to FORMAT ONLY (no new facts)
            full_md = self._format_full_plan_ai(profile, ui_programs, analysis, timeline_events, projects)

            return ServiceResult.success(
                message=full_md,
                data={
                    "programs": ui_programs,
                    "analysis": analysis,
                    "timeline_events": timeline_events,
                    "projects": projects,
                    "md": full_md,
                },
            )

        except Exception as e:
            logger.error(f"Roadmap generate error: {e}")
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

        prereq_raw = g(prog, "prerequisites", "") or ""
        admission_raw = g(prog, "admission_average", "") or ""

        missing = bd.get("missing_prereqs", []) if isinstance(bd, dict) else []
        missing = [str(x).strip() for x in (missing or []) if str(x).strip()]

        return {
            "program_name": g(prog, "program_name", "") or "",
            "university_name": g(prog, "university_name", "") or g(prog, "university", "") or "",
            "program_url": g(prog, "program_url", "") or g(prog, "url", "") or "",
            "admission_average": str(admission_raw).strip(),
            "prerequisites": _clean_prereq_display(str(prereq_raw)),
            "co_op_available": bool(g(prog, "co_op_available", False) or g(prog, "coop_available", False)),
            "match_percent": match_percent,
            "missing_prereqs": missing,
            "grade_assessment": bd.get("grade_assessment") if isinstance(bd, dict) else None,
        }

    def _build_timeline(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """
        Timeline = date-based milestones (unique vs checklist).
        Anchors to OUAC equal consideration deadline (Jan 15).
        """
        today = date.today()
        deadline = _parse_ouac_deadline()

        # simple milestone spacing
        days_left = max(0, (deadline - today).days)
        return [
            {
                "date": _iso(today),
                "title": "Today",
                "items": [
                    "Confirm your top 6 Grade 12 U/M courses",
                    "Pick 6–10 programs (mix of safe/target/reach)",
                ],
            },
            {
                "date": _iso(min(deadline, today.replace(day=min(today.day + 7, 28)))),
                "title": "Within 7 days",
                "items": [
                    "Draft your shortlist and save each program link",
                    "Start a small portfolio/project log (Google Doc or Notion)",
                ],
            },
            {
                "date": _iso(deadline),
                "title": "OUAC Equal Consideration Deadline (Jan 15)",
                "items": [
                    "Submit applications for equal consideration",
                    "Double-check supplementary requirements (if any) per school/program",
                ],
                "meta": {"days_left": days_left},
            },
        ]

    def _build_projects(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """
        Checklist = supplementary boosters (unique vs timeline).
        """
        interest = (profile.interests or "").lower()

        projects = []

        # Robotics / engineering flavored defaults
        if "robot" in interest or "mechat" in interest or "engineering" in interest:
            projects.append({
                "title": "Robotics Portfolio Project (2–3 weeks)",
                "items": [
                    "Build one small robotics project (Arduino / Raspberry Pi / simulation)",
                    "Write a 1-page project summary (goal, design, results, what you learned)",
                    "Add photos/video + GitHub link (if coding)",
                ],
            })
            projects.append({
                "title": "Competition / Club Impact (ongoing)",
                "items": [
                    "Join (or lead) a robotics/engineering club and take ownership of one subsystem",
                    "Log measurable impact: prototypes built, tests run, features shipped",
                    "Ask a mentor/teacher for a short reference note about your role",
                ],
            })
        else:
            projects.append({
                "title": "Interest Portfolio (2–3 weeks)",
                "items": [
                    "Create one tangible artifact: mini-research brief, app, case study, or design",
                    "Document process + reflection (what changed after feedback)",
                    "Publish it somewhere linkable (Drive/Notion/GitHub)",
                ],
            })

        projects.append({
            "title": "Supplementary Application Pack",
            "items": [
                "Prepare a master activities list (role, dates, impact, links)",
                "Draft 3–5 story bullets (challenge → action → result → lesson)",
                "Collect 2 references who can speak to your work ethic and growth",
            ],
        })

        return projects[:6]

    def _format_full_plan_ai(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis: str,
        timeline_events: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        """
        Uses LLM to format ONLY. If no API, falls back to deterministic markdown.
        """
        payload = {
            "profile": {
                "interest": profile.interests,
                "grade": profile.grade,
                "average": profile.average,
                "subjects": profile.subjects,
                "location": profile.location,
            },
            "programs": ui_programs[:10],
            "timeline_events": timeline_events,
            "projects": projects,
            "analysis": analysis,
        }

        if not self.llm.has_api:
            return self._format_full_plan_fallback(payload)

        system = (
            "You are formatting structured data into clean Markdown.\n"
            "RULES:\n"
            "- Do NOT add new facts.\n"
            "- Do NOT invent deadlines beyond what is provided.\n"
            "- Keep prerequisites short (use given text).\n"
            "- Output ONLY Markdown.\n"
        )
        prompt = (
            "Format this into a polished student-friendly plan with these sections:\n"
            "1) Profile\n"
            "2) Top Programs (table)\n"
            "3) Timeline (dated bullets)\n"
            "4) Checklist Projects (checkbox style)\n"
            "5) Personalized Analysis (lightly cleaned)\n\n"
            f"DATA:\n{payload}"
        )
        out = (self.llm.generate(prompt, system) or "").strip()
        return out or self._format_full_plan_fallback(payload)

    def _format_full_plan_fallback(self, payload: Dict[str, Any]) -> str:
        p = payload["profile"]
        lines = []
        lines.append("## ✨ Your Personalized University Roadmap\n")
        lines.append(f"**🎯 Interest:** {p.get('interest','')}  ")
        lines.append(f"**📊 Grade:** {p.get('grade','')} | **Average:** {p.get('average','')}%  ")
        subj = ", ".join((p.get("subjects") or [])[:6]) or "Not specified"
        lines.append(f"**📚 Subjects:** {subj}\n")
        lines.append("---\n")

        lines.append("## Top Matching Programs\n")
        lines.append("| # | Program | University | Match | Co-op | Prereqs (db) |")
        lines.append("|---:|---|---|---:|:---:|---|")
        for i, pr in enumerate(payload["programs"], 1):
            lines.append(
                f"| {i} | {pr.get('program_name','')} | {pr.get('university_name','')} | {pr.get('match_percent',0)}% | "
                f\"{'✅' if pr.get('co_op_available') else '—'}\" + f" | {pr.get('prerequisites','')} |"
            )
        lines.append("\n---\n")

        lines.append("## Timeline\n")
        for ev in payload["timeline_events"]:
            lines.append(f"**{ev.get('date','')} — {ev.get('title','')}**")
            for it in ev.get("items", [])[:8]:
                lines.append(f"- {it}")
            lines.append("")
        lines.append("---\n")

        lines.append("## Checklist Projects\n")
        for ph in payload["projects"]:
            lines.append(f"**{ph.get('title','')}**")
            for it in ph.get("items", [])[:10]:
                lines.append(f"- [ ] {it}")
            lines.append("")
        lines.append("---\n")

        lines.append("## Personalized Analysis\n")
        lines.append(payload.get("analysis") or "- No analysis returned.")
        return "\n".join(lines).strip()