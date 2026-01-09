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
import json
from datetime import date, timedelta
from typing import List, Dict, Any

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")

COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3}\d[A-Za-z])\b")  # e.g., MHF4U, SCH4U, SPH4U


def _parse_ouac_deadline() -> date:
    """
    Equal consideration is typically Jan 15.
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
    out, seen = [], set()
    for h in hits:
        h = h.replace("O", "0")  # just in case
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


def _json_default(o):
    """Allow json.dumps() to handle numpy-ish scalars, sets, bytes, etc."""
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except Exception:
        pass

    if isinstance(o, set):
        return list(o)

    if isinstance(o, (bytes, bytearray)):
        try:
            return o.decode("utf-8")
        except Exception:
            return str(o)

    return str(o)


class RoadmapService:
    def __init__(self, config: Config, llm_client: LLMClient, program_search: ProgramSearchService):
        self.config = config
        self.llm = llm_client
        self.search = program_search
        self.prompts = PromptTemplates()

    # =========================
    # MAIN GENERATE
    # =========================
    def generate(self, profile: StudentProfile, session: Session) -> ServiceResult:
        try:
            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            if not results:
                return ServiceResult.failure("No programs found.")

            programs_for_prompt = [p for p, _, _ in results]

            # 1) AI ANALYSIS (content) — this is your “reasoning” section
            prompt = self.prompts.roadmap_prompt(profile, programs_for_prompt)
            analysis = (self.llm.generate(prompt, self.prompts.roadmap_system_prompt()) or "").strip()

            # 2) UI programs (cleaned + compact)
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            # 3) UNIQUE TABS:
            #    - timeline_events: dated milestones (today → Jan 15)
            #    - projects: supplementary / portfolio checklist
            timeline_events = self._build_timeline(profile)
            projects = self._build_projects(profile)

            # 4) Full plan markdown — AI formats only (no new facts)
            full_md = self._format_full_plan_ai(profile, ui_programs, analysis, timeline_events, projects)

            return ServiceResult.success(
                message=full_md,
                data={
                    "md": full_md,
                    "programs": ui_programs,
                    "analysis": analysis,
                    "timeline_events": timeline_events,
                    "projects": projects,
                },
            )

        except Exception as e:
            logger.error(f"Roadmap generate error: {e}")
            return ServiceResult.failure(str(e))

    # =========================
    # PROGRAM PAYLOAD
    # =========================
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
            "grade_assessment": bd.get("grade_assessment") if isinstance(bd, dict) else None,
        }

    # =========================
    # TIMELINE (DATED)
    # =========================
    def _build_timeline(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """
        Timeline tab = date-based milestones (NOT a checklist).
        Anchors to Jan 15 “equal consideration” target.
        """
        today = date.today()
        deadline = _parse_ouac_deadline()

        # milestones (cap each at deadline)
        def cap(d: date) -> date:
            return d if d <= deadline else deadline

        milestones = [
            (today, "Today", [
                "Confirm your top 6 Grade 12 U/M courses (and your prerequisites).",
                "Pick 6–10 programs (mix of safe/target/reach).",
            ]),
            (cap(today + timedelta(days=7)), "Within 7 days", [
                "Save links + requirements for each shortlisted program.",
                "Start a simple tracker: program, prerequisites, admission notes, link.",
            ]),
            (cap(today + timedelta(days=21)), "Within 3 weeks", [
                "Finalize your shortlist (aim 6–10).",
                "Identify any supplementary pieces (forms, interviews, portfolios) for each school.",
            ]),
            (deadline, "OUAC Equal Consideration Target (Jan 15)", [
                "Submit applications for equal consideration (where applicable).",
                "Re-check each program page for updated requirements close to submit time.",
            ]),
        ]

        # remove duplicate dates (e.g., if close to deadline)
        seen_dates = set()
        events: List[Dict[str, Any]] = []
        for d, title, items in milestones:
            ds = _iso(d)
            if ds in seen_dates:
                continue
            seen_dates.add(ds)
            events.append({"date": ds, "title": title, "items": items})

        # add days left meta (optional)
        days_left = max(0, (deadline - today).days)
        events[-1]["meta"] = {"days_left": days_left}

        return events[:10]

    # =========================
    # PROJECT CHECKLIST (SUPP / PORTFOLIO)
    # =========================
    def _build_projects(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """
        Checklist tab = projects + proof-of-interest tasks (unique vs timeline).
        """
        interest = (profile.interests or "").lower()

        blocks: List[Dict[str, Any]] = []

        # Engineering / Robotics
        if any(k in interest for k in ["robot", "mechat", "engineering", "automation"]):
            blocks.append({
                "title": "Robotics / Engineering Portfolio Project (2–3 weeks)",
                "items": [
                    "Build one small project (Arduino / sensor system / CAD mechanism / simulation).",
                    "Write a 1-page summary: goal → design → tests → results → what you learned.",
                    "Add proof: photos/video + diagram + code link (GitHub if possible).",
                ],
            })
            blocks.append({
                "title": "Supplementary Strength (ongoing)",
                "items": [
                    "Join/lead a club team and own one subsystem (controls, CAD, electronics, testing).",
                    "Track measurable impact (tests run, iterations, parts designed, bugs fixed).",
                    "Ask a mentor/teacher for a short reference note about your contributions.",
                ],
            })

        # Computer Science
        elif any(k in interest for k in ["computer", "software", "cs", "ai", "data"]):
            blocks.append({
                "title": "Build + Ship a Mini App (2–3 weeks)",
                "items": [
                    "Build one app (web tool, bot, data dashboard) related to your interest.",
                    "Write a README: problem, approach, features, screenshots, next steps.",
                    "Deploy or publish (GitHub + optional live demo link).",
                ],
            })

        # Health/Life sciences
        elif any(k in interest for k in ["health", "bio", "medical", "life", "neuro"]):
            blocks.append({
                "title": "Research / Evidence Project (2–3 weeks)",
                "items": [
                    "Pick a topic + write a 1–2 page brief using credible sources.",
                    "Summarize: what’s known, what’s debated, and your conclusion.",
                    "Present it (club talk / poster / short video) and keep a linkable copy.",
                ],
            })

        # Default
        else:
            blocks.append({
                "title": "Interest Portfolio (2–3 weeks)",
                "items": [
                    "Create one tangible artifact (case study, design, mini research brief, app).",
                    "Document: first version → feedback → improved version.",
                    "Publish somewhere linkable (Drive/Notion/GitHub).",
                ],
            })

        # Common “supp pack”
        blocks.append({
            "title": "Supplementary Application Pack (high leverage)",
            "items": [
                "Make a master activities list (role, dates, impact, links).",
                "Write 3–5 story bullets: challenge → action → result → lesson.",
                "Prepare a clean folder of evidence: certificates, photos, write-ups, links.",
            ],
        })

        return blocks[:8]

    # =========================
    # FULL PLAN FORMATTING
    # =========================
    def _format_full_plan_ai(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis: str,
        timeline_events: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        """
        LLM formats ONLY (no new facts). If no API, fallback deterministic markdown.
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

        if not getattr(self.llm, "has_api", False):
            return self._format_full_plan_fallback(payload)

        system = (
            "You are polishing and lightly cleaning Markdown that already follows a fixed template.\n"
            "RULES:\n"
            "- Do NOT change the template structure.\n"
            "- Do NOT convert into numbered outline sections like '1) Profile'.\n"
            "- Do NOT create tables.\n"
            "- Keep program blocks as '### 1. Program Name' style.\n"
            "- You may only:\n"
            "  (a) fix spacing/line breaks,\n"
            "  (b) remove duplicate commas/extra spaces,\n"
            "  (c) make bullets cleaner,\n"
            "  (d) shorten overly long prereq/admission text WITHOUT adding facts.\n"
            "- Output ONLY Markdown.\n"
        )

        payload_json = json.dumps(payload, ensure_ascii=False, default=_json_default)

        prompt = (
            "Take the following DATA and fill it into the EXACT TEMPLATE below.\n"
            "Keep headings and separators exactly.\n\n"
            "TEMPLATE:\n"
            "## ✨ Your Personalized University Roadmap\n"
            "\n"
            "**🎯 Interest:** {interest}\n"
            "**📊 Grade:** {grade} | **Average:** {average}%\n"
            "**📚 Subjects:** {subjects}\n"
            "\n"
            "---\n"
            "\n"
            "## Top Matching Programs\n"
            "{program_blocks}\n"
            "\n"
            "---\n"
            "\n"
            "## Personalized Analysis\n"
            "{analysis}\n"
            "\n"
            "---\n"
            "\n"
            "## Timeline\n"
            "{timeline}\n"
            "\n"
            "---\n"
            "\n"
            "## Checklist Projects\n"
            "{projects}\n"
            "\n"
            "---\n"
            "**Tip:** Always verify prerequisites/admission details using the program link (requirements can change).\n\n"
            f"DATA:\n{payload}"
        )

        out = (self.llm.generate(prompt, system) or "").strip()
        return out or self._format_full_plan_fallback(payload)

    def _format_full_plan_fallback(self, payload: Dict[str, Any]) -> str:
        p = payload["profile"]
        lines: List[str] = []

        lines.append("## ✨ Your Personalized University Roadmap\n")
        lines.append(f"**🎯 Interest:** {p.get('interest','')}  ")
        lines.append(f"**📊 Grade:** {p.get('grade','')} | **Average:** {p.get('average','')}%  ")
        subj = ", ".join((p.get("subjects") or [])[:6]) or "Not specified"
        lines.append(f"**📚 Subjects:** {subj}\n")
        lines.append("---\n")

        lines.append("## Top Matching Programs\n")
        lines.append("| Program | University | Match | Co-op | Prereqs (db) |")
        lines.append("|---|---|---:|:---:|---|")
        for pr in payload["programs"]:
            coop_mark = "✅" if pr.get("co_op_available") else "—"
            lines.append(
                f"| {pr.get('program_name','')} | {pr.get('university_name','')} | "
                f"{pr.get('match_percent',0)}% | {coop_mark} | {pr.get('prerequisites','')} |"
            )
        lines.append("\n---\n")

        lines.append("## Timeline\n")
        for ev in payload["timeline_events"]:
            lines.append(f"**{ev.get('date','')} — {ev.get('title','')}**")
            for it in ev.get("items", [])[:10]:
                lines.append(f"- {it}")
            lines.append("")
        lines.append("---\n")

        lines.append("## Checklist Projects\n")
        for blk in payload["projects"]:
            lines.append(f"**{blk.get('title','')}**")
            for it in blk.get("items", [])[:12]:
                lines.append(f"- [ ] {it}")
            lines.append("")
        lines.append("---\n")

        lines.append("## Personalized Analysis\n")
        lines.append(payload.get("analysis") or "- No analysis returned.")
        return "\n".join(lines).strip()

    # =========================
    # FOLLOWUP (unchanged; you can expand later)
    # =========================
    def followup(self, question: str, session: Session) -> ServiceResult:
        try:
            context = session.last_profile.to_context_string() if session.last_profile else ""
            prompt = self.prompts.followup_prompt(question, context)
            response = self.llm.generate(prompt, self.prompts.followup_system_prompt())
            return ServiceResult.success(message=response) if response else ServiceResult.failure("No response")
        except Exception as e:
            return ServiceResult.failure(str(e))