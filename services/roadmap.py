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
from datetime import date, timedelta
from typing import List, Dict, Any

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")

COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3}\d[A-Za-z])\b")

def _parse_ouac_deadline() -> date:
    today = date.today()
    dl = date(today.year, 1, 15)
    if today > dl:
        dl = date(today.year + 1, 1, 15)
    return dl

def _clean_course_codes(text: str) -> List[str]:
    if not text:
        return []
    hits = [m.group(1).upper() for m in COURSE_CODE_RE.finditer(text)]
    out, seen = [], set()
    for h in hits:
        h = h.replace("O", "0")
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:12]

def _clean_prereq_display(text: str) -> str:
    codes = _clean_course_codes(text or "")
    if codes:
        return ", ".join(codes)
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

            # LLM analysis content (not formatting)
            prompt = self.prompts.roadmap_prompt(profile, programs_for_prompt)
            analysis = (self.llm.generate(prompt, self.prompts.roadmap_system_prompt()) or "").strip()

            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            timeline_events = self._build_timeline(profile)
            projects = self._build_projects(profile)

            full_md = self._format_full_plan(profile, ui_programs, analysis, timeline_events, projects)

            return ServiceResult.success(
                message=full_md,
                data={
                    "md": full_md,
                    "profile": {
                        "interest": profile.interests,
                        "grade": profile.grade,
                        "avg": profile.average,
                        "subjects": ", ".join((profile.subjects or [])[:6]),
                    },
                    "programs": ui_programs,
                    "timeline_events": timeline_events,
                    "projects": projects,
                    "analysis": analysis,
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
            "admission_average": str(admission_raw).strip() or "Check website",
            "prerequisites": _clean_prereq_display(str(prereq_raw)),
            "co_op_available": bool(g(prog, "co_op_available", False) or g(prog, "coop_available", False)),
            "match_percent": match_percent,
            "missing_prereqs": missing,
        }

    def _build_timeline(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        today = date.today()
        deadline = _parse_ouac_deadline()
        days_left = max(0, (deadline - today).days)

        def d(n: int) -> str:
            return (today + timedelta(days=n)).isoformat()

        def before_deadline(n: int) -> str:
            return (deadline - timedelta(days=n)).isoformat()

        events = []
        events.append({
            "date": today.isoformat(),
            "title": "Start (today)",
            "items": [
                "Confirm your top 6 Grade 12 U/M courses + prerequisites",
                "Create a shortlist tracker (program, link, prereqs, admission notes, supp apps)",
                "Pick 6–10 programs (safe / target / reach)",
            ],
            "meta": {"days_left": days_left},
        })

        if days_left <= 10:
            events += [
                {"date": d(1), "title": "Within 24 hours", "items": [
                    "Open each program link and verify prerequisites + competitive averages",
                    "Identify which programs require supplementary applications / interviews",
                ]},
                {"date": d(3), "title": "Within 3 days", "items": [
                    "Finalize your program list (avoid daily switching)",
                    "Prepare your activities list (role → impact → proof links)",
                ]},
                {"date": before_deadline(1), "title": "Day before OUAC (buffer)", "items": [
                    "Final review: personal info, grades, program choices, payment",
                    "Save confirmation details (screenshot + tracker notes)",
                ]},
            ]
        else:
            events += [
                {"date": d(3), "title": "Within 72 hours", "items": [
                    "Verify prerequisites for each program and remove mismatches",
                    "Create a ‘supplementary requirements’ checklist per school",
                ]},
                {"date": d(7), "title": "1 week", "items": [
                    "Lock shortlist (aim 8–12) and categorize safe/target/reach",
                    "Start 1 portfolio artifact (project write-up / design / GitHub)",
                ]},
                {"date": d(14), "title": "2 weeks", "items": [
                    "Draft 3–5 impact stories (challenge → action → result → lesson)",
                    "Ask 1–2 mentors/teachers for reference support (if needed)",
                ]},
                {"date": before_deadline(7), "title": "1 week before OUAC", "items": [
                    "Submit early if possible (avoid last-minute technical issues)",
                    "Confirm supplementary portals + deadlines after submission",
                ]},
            ]

        events.append({
            "date": deadline.isoformat(),
            "title": "OUAC Equal Consideration (Jan 15)",
            "items": [
                "Submit for equal consideration",
                "Confirm submission + save receipt/confirmation",
                "Immediately check next steps: portals + supplementary deadlines",
            ],
            "meta": {"days_left": days_left},
        })

        # Deduplicate by date
        seen = set()
        clean = []
        for e in events:
            if e["date"] in seen:
                continue
            seen.add(e["date"])
            clean.append(e)
        return clean[:10]

    def _build_projects(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        interest = (profile.interests or "").lower()

        projects = []

        if any(k in interest for k in ["robot", "mechat", "engineering", "mechanical", "electrical", "automation"]):
            projects.append({
                "title": "Engineering / Robotics Showcase (best differentiator)",
                "items": [
                    "Build ONE small system (Arduino + sensor, CAD mechanism, control loop, or simulation)",
                    "Document tests (before/after, performance numbers, failures + fixes)",
                    "Create a 60–90s demo video + link it in your tracker",
                    "Optional: publish to GitHub with a clean README",
                ],
            })
            projects.append({
                "title": "Club / Competition Impact (ongoing)",
                "items": [
                    "Join/lead a team and own one subsystem (CAD, electronics, controls, testing)",
                    "Track measurable impact (iterations shipped, tests run, parts designed)",
                    "Ask a mentor/teacher for 2–3 sentence reference note about your role",
                ],
            })
        else:
            projects.append({
                "title": "Portfolio Artifact (1–2 weeks)",
                "items": [
                    "Create ONE tangible artifact: mini research brief, app, case study, or design",
                    "Document process + reflection (what changed after feedback)",
                    "Publish it somewhere linkable (Drive/Notion/GitHub)",
                ],
            })

        projects.append({
            "title": "Application Strength Pack (high leverage)",
            "items": [
                "Create a master activities list (role, dates, impact, proof link)",
                "Write 5 story bullets (challenge → action → result → lesson)",
                "Prepare a clean evidence folder (certificates, photos, write-ups, links)",
                "Draft 1 short ‘why this program’ paragraph template (editable per school)",
            ],
        })

        projects.append({
            "title": "Scholarships & Finance (easy wins)",
            "items": [
                "List 5 scholarships you qualify for + deadlines",
                "Prepare a reusable scholarship paragraph (impact + leadership + growth)",
                "Estimate cost for top 3 schools (tuition + residence + transport)",
            ],
        })

        return projects[:8]

    def _format_full_plan(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis_md: str,
        timeline_events: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        subj = ", ".join((profile.subjects or [])[:5]) if profile.subjects else "Not specified"

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
        lines.append("## Actionable Next Steps (Timeline)")
        lines.append("")
        for ev in timeline_events[:10]:
            lines.append(f"**{ev.get('date','')} — {ev.get('title','')}**")
            for it in (ev.get("items") or [])[:10]:
                lines.append(f"- {it}")
            lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Portfolio & Supplementary Checklist")
        lines.append("")
        for sec in projects[:8]:
            lines.append(f"**{sec.get('title','')}**")
            for it in (sec.get("items") or [])[:12]:
                lines.append(f"- [ ] {it}")
            lines.append("")
        lines.append("---")
        lines.append("**Tip:** Always verify prerequisites/admission details using the program link (requirements can change).")

        return "\n".join(lines).strip()
