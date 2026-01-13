'''
# services/roadmap.py
import logging
import re
import json
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")

COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3}\d[A-Za-z])\b")  # e.g., MHF4U, SCH4U, SPH4U

def _parse_ouac_deadline(grade: str = "Grade 12") -> date:
    """
    Calculate OUAC equal consideration deadline based on student's current grade.
    
    - Grade 12 → This school year's Jan 15 (or next if already passed)
    - Grade 11 → Next year's Jan 15
    - Grade 10 → Jan 15 in 2 years
    - Grade 9 → Jan 15 in 3 years
    """
    today = date.today()
    current_year = today.year
    
    # Determine the school year
    # If we're in Sept-Dec, we're in the fall semester of school year X/X+1
    # If we're in Jan-Aug, we're in the spring semester of school year X-1/X
    if today.month >= 9:
        # Fall semester: school year is current_year / current_year+1
        # Grade 12 students apply Jan 15 of current_year+1
        base_deadline_year = current_year + 1
    else:
        # Spring semester: school year is current_year-1 / current_year
        # Grade 12 students apply Jan 15 of current_year
        base_deadline_year = current_year
    
    # Adjust based on grade
    grade_lower = (grade or "").lower()
    
    if "12" in grade_lower or "gap" in grade_lower or "university" in grade_lower:
        # Grade 12, Gap Year, or University Transfer - deadline is this cycle
        years_until_deadline = 0
    elif "11" in grade_lower:
        # Grade 11 - deadline is next year
        years_until_deadline = 1
    elif "10" in grade_lower:
        # Grade 10 - deadline is in 2 years
        years_until_deadline = 2
    elif "9" in grade_lower:
        # Grade 9 - deadline is in 3 years
        years_until_deadline = 3
    else:
        # Default to current cycle
        years_until_deadline = 0
    
    deadline_year = base_deadline_year + years_until_deadline
    deadline = date(deadline_year, 1, 15)
    
    # If the calculated deadline has already passed (edge case), move to next year
    if deadline < today:
        deadline = date(deadline_year + 1, 1, 15)
    
    return deadline

###
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
###

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
    def generate(self, profile: StudentProfile, session: Session, timeline_context: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """
        Generate roadmap with optional timeline context for mode-aware generation.
        Now with graceful fallback when LLM is unavailable.
        """
        try:
            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            if not results:
                return ServiceResult.failure("No programs found.")
    
            programs_for_prompt = [p for p, _, _ in results]
    
            # 1) Try AI ANALYSIS - but handle failures gracefully
            analysis = self._generate_analysis_safe(profile, programs_for_prompt)
    
            # 2) UI programs (cleaned + compact)
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]
    
            # 3) Timeline and projects (deterministic - always works)
            timeline_events = self._build_timeline(profile)
            projects = self._build_projects(profile)
    
            # 4) Detect mode from timeline_context (if provided)
            mode = "exploration"  # default
            mode_info = {
                "emoji": "🔍",
                "label": "Exploration Mode",
                "description": "Keeping doors open while you figure things out.",
                "color": "#3b82f6"
            }
            
            if timeline_context:
                mode = self._detect_mode(timeline_context, profile)
                mode_info = self._get_mode_info(mode)
    
            # 5) Full plan markdown - use fallback if LLM unavailable
            full_md = self._format_full_plan_safe(profile, ui_programs, analysis, timeline_events, projects)
    
            return ServiceResult.success(
                message=full_md,
                data={
                    "md": full_md,
                    "programs": ui_programs,
                    "analysis": analysis,
                    "timeline_events": timeline_events,
                    "projects": projects,
                    "mode": mode,
                    "mode_info": mode_info,
                },
            )
    
        except Exception as e:
            logger.error(f"Roadmap generate error: {e}")
            return ServiceResult.failure(str(e))
    
    def _generate_analysis_safe(self, profile: StudentProfile, programs: List[Program]) -> str:
        """
        Generate AI analysis with graceful fallback on API errors.
        """
        try:
            prompt = self.prompts.roadmap_prompt(profile, programs)
            response = self.llm.generate(prompt, self.prompts.roadmap_system_prompt())
            if response and response.strip():
                return response.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "503" in error_str or "overloaded" in error_str or "unavailable" in error_str:
                logger.warning(f"LLM overloaded, using fallback analysis: {e}")
            elif "429" in error_str or "quota" in error_str or "rate" in error_str:
                logger.warning(f"LLM rate limited, using fallback analysis: {e}")
            else:
                logger.error(f"LLM analysis failed: {e}")
        
        # Return fallback analysis
        return self._build_fallback_analysis(profile, programs)
    
    def _build_fallback_analysis(self, profile: StudentProfile, programs: List[Program]) -> str:
        """
        Build a deterministic analysis when LLM is unavailable.
        """
        interest = profile.interests or "your selected fields"
        grade = profile.grade or "your current grade"
        avg = profile.average or 80
        
        # Determine admission outlook
        if avg >= 90:
            outlook = "Your strong average opens doors to competitive programs. Focus on supplementary applications to stand out."
        elif avg >= 85:
            outlook = "Your average is competitive for most programs. Consider both target and reach schools in your shortlist."
        elif avg >= 80:
            outlook = "Your average is solid. Focus on programs where you're within the admission range, and include some safer options."
        elif avg >= 75:
            outlook = "Consider programs with admission averages in the mid-70s to low-80s range. College transfer pathways are also worth exploring."
        else:
            outlook = "Focus on improving your grades this semester. Also explore college programs with university transfer agreements."
        
        # Build program-specific advice
        program_names = [p.program_name for p in programs[:3]] if programs else ["your target programs"]
        programs_str = ", ".join(program_names)
        
        analysis = f"""### Your Profile Assessment
    
    **Interests:** {interest}
    **Current Standing:** {grade} with {avg}% average
    
    ### Admission Outlook
    {outlook}
    
    ### Recommended Focus Areas
    
    1. **Prerequisites:** Verify you have all required courses for {programs_str}. Missing prerequisites are the #1 reason for application rejection.
    
    2. **Supplementary Applications:** Many competitive programs require essays, portfolios, or interviews. Start preparing these early.
    
    3. **Extracurriculars:** Quality over quantity. Deep involvement in 2-3 activities is better than surface-level participation in many.
    
    4. **Backup Planning:** Always have safe, target, and reach schools in your list. Don't put all your eggs in one basket.
    
    ### Next Steps
    - Review the program cards below to understand admission requirements
    - Use the timeline to stay on track with deadlines
    - Complete the checklist items to build a strong application
    
    *Note: Personalized AI analysis temporarily unavailable. This is general guidance based on your profile.*
    """
        
        return analysis
    
    def _format_full_plan_safe(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis: str,
        timeline_events: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        """
        Format full plan with graceful fallback if LLM formatting fails.
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
    
        # If no API key or LLM not available, use fallback immediately
        if not getattr(self.llm, "has_api", False):
            return self._format_full_plan_fallback(payload)
    
        # Try LLM formatting, but fall back on any error
        try:
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
                f"DATA:\n{payload_json}"
            )
    
            out = self.llm.generate(prompt, system)
            if out and out.strip():
                return out.strip()
                
        except Exception as e:
            logger.warning(f"LLM formatting failed, using fallback: {e}")
    
        # Fallback to deterministic formatting
        return self._format_full_plan_fallback(payload)
    
###
    def generate(self, profile: StudentProfile, session: Session, timeline_context: Optional[Dict[str, Any]] = None) -> ServiceResult:
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
###
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
        deadline = _parse_ouac_deadline(profile.grade)
    
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
'''
# services/roadmap.py
import logging
import re
import json
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from config import Config
from models import StudentProfile, Session, ServiceResult, Program
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from prompts.templates import PromptTemplates

logger = logging.getLogger("saarthi.roadmap")

COURSE_CODE_RE = re.compile(r"\b([A-Za-z]{3}\d[A-Za-z])\b")


def _parse_ouac_deadline(grade: str = "Grade 12") -> date:
    """
    Calculate OUAC equal consideration deadline based on student's current grade.
    """
    today = date.today()
    current_year = today.year
    
    if today.month >= 9:
        base_deadline_year = current_year + 1
    else:
        base_deadline_year = current_year
    
    grade_lower = (grade or "").lower()
    
    if "12" in grade_lower or "gap" in grade_lower or "university" in grade_lower:
        years_until_deadline = 0
    elif "11" in grade_lower:
        years_until_deadline = 1
    elif "10" in grade_lower:
        years_until_deadline = 2
    elif "9" in grade_lower:
        years_until_deadline = 3
    else:
        years_until_deadline = 0
    
    deadline_year = base_deadline_year + years_until_deadline
    deadline = date(deadline_year, 1, 15)
    
    if deadline < today:
        deadline = date(deadline_year + 1, 1, 15)
    
    return deadline


def _iso(d: date) -> str:
    return d.isoformat()


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
    def generate(self, profile: StudentProfile, session: Session, timeline_context: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """
        Generate roadmap with optional timeline context for mode-aware generation.
        Now with graceful fallback when LLM is unavailable.
        """
        try:
            results = self.search.search_with_profile(profile, self.config.TOP_K_PROGRAMS)
            if not results:
                return ServiceResult.failure("No programs found.")

            programs_for_prompt = [p for p, _, _ in results]

            # 1) Try AI ANALYSIS - but handle failures gracefully
            analysis = self._generate_analysis_safe(profile, programs_for_prompt)

            # 2) UI programs (cleaned + compact)
            ui_programs = [self._program_to_payload(p, score, bd) for (p, score, bd) in results]

            # 3) Timeline and projects (deterministic - always works)
            timeline_events = self._build_timeline(profile)
            projects = self._build_projects(profile)

            # 4) Detect mode from timeline_context (if provided)
            mode = "exploration"
            mode_info = {
                "emoji": "🔍",
                "label": "Exploration Mode",
                "description": "Keeping doors open while you figure things out.",
                "color": "#3b82f6"
            }
            
            if timeline_context:
                mode = self._detect_mode(timeline_context, profile)
                mode_info = self._get_mode_info(mode)

            # 5) Full plan markdown - use fallback if LLM unavailable
            full_md = self._format_full_plan_safe(profile, ui_programs, analysis, timeline_events, projects)

            return ServiceResult.success(
                message=full_md,
                data={
                    "md": full_md,
                    "programs": ui_programs,
                    "analysis": analysis,
                    "timeline_events": timeline_events,
                    "projects": projects,
                    "mode": mode,
                    "mode_info": mode_info,
                },
            )

        except Exception as e:
            logger.error(f"Roadmap generate error: {e}")
            return ServiceResult.failure(str(e))

    # =========================
    # SAFE LLM CALLS
    # =========================
    def _generate_analysis_safe(self, profile: StudentProfile, programs: List[Program]) -> str:
        """Generate AI analysis with graceful fallback on API errors."""
        try:
            prompt = self.prompts.roadmap_prompt(profile, programs)
            response = self.llm.generate(prompt, self.prompts.roadmap_system_prompt())
            if response and response.strip():
                return response.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "503" in error_str or "overloaded" in error_str or "unavailable" in error_str:
                logger.warning(f"LLM overloaded, using fallback analysis: {e}")
            elif "429" in error_str or "quota" in error_str or "rate" in error_str:
                logger.warning(f"LLM rate limited, using fallback analysis: {e}")
            else:
                logger.error(f"LLM analysis failed: {e}")
        
        return self._build_fallback_analysis(profile, programs)

    def _build_fallback_analysis(self, profile: StudentProfile, programs: List[Program]) -> str:
        """Build a deterministic analysis when LLM is unavailable."""
        interest = profile.interests or "your selected fields"
        grade = profile.grade or "your current grade"
        avg = profile.average or 80
        
        if avg >= 90:
            outlook = "Your strong average opens doors to competitive programs. Focus on supplementary applications to stand out."
        elif avg >= 85:
            outlook = "Your average is competitive for most programs. Consider both target and reach schools in your shortlist."
        elif avg >= 80:
            outlook = "Your average is solid. Focus on programs where you're within the admission range, and include some safer options."
        elif avg >= 75:
            outlook = "Consider programs with admission averages in the mid-70s to low-80s range. College transfer pathways are also worth exploring."
        else:
            outlook = "Focus on improving your grades this semester. Also explore college programs with university transfer agreements."
        
        program_names = [p.program_name for p in programs[:3]] if programs else ["your target programs"]
        programs_str = ", ".join(program_names)
        
        analysis = f"""### Your Profile Assessment

**Interests:** {interest}
**Current Standing:** {grade} with {avg}% average

### Admission Outlook
{outlook}

### Recommended Focus Areas

1. **Prerequisites:** Verify you have all required courses for {programs_str}. Missing prerequisites are the #1 reason for application rejection.

2. **Supplementary Applications:** Many competitive programs require essays, portfolios, or interviews. Start preparing these early.

3. **Extracurriculars:** Quality over quantity. Deep involvement in 2-3 activities is better than surface-level participation in many.

4. **Backup Planning:** Always have safe, target, and reach schools in your list.

### Next Steps
- Review the program cards below to understand admission requirements
- Use the timeline to stay on track with deadlines
- Complete the checklist items to build a strong application

*Note: Personalized AI analysis temporarily unavailable. This is general guidance based on your profile.*
"""
        return analysis

    # =========================
    # MODE DETECTION
    # =========================
    def _detect_mode(self, ctx: Dict[str, Any], profile: StudentProfile) -> str:
        """Detect timeline mode from context"""
        academic_status = ctx.get("academic_status", "on-track")
        confidence_level = ctx.get("confidence_level", 3)
        target_programs = ctx.get("target_programs", [])
        missing_prereqs = ctx.get("missing_prereqs", [])
        
        if (profile.average < 75 or 
            academic_status == "behind" or 
            len(missing_prereqs) >= 2):
            return "catchup"
        
        if (target_programs and len(target_programs) > 0 and confidence_level >= 4):
            return "trajectory"
        
        if confidence_level >= 4 and profile.interests:
            return "trajectory"
        
        return "exploration"

    def _get_mode_info(self, mode: str) -> Dict[str, Any]:
        """Get mode display info"""
        modes = {
            "trajectory": {
                "emoji": "🎯",
                "label": "Trajectory Mode",
                "description": "You know where you're going. Let's map the fastest path.",
                "color": "#22c55e"
            },
            "exploration": {
                "emoji": "🔍",
                "label": "Exploration Mode",
                "description": "Keeping doors open while you figure things out.",
                "color": "#3b82f6"
            },
            "catchup": {
                "emoji": "🚀",
                "label": "Catch-up Mode",
                "description": "Recovery plan to get you back on track.",
                "color": "#f97316"
            }
        }
        return modes.get(mode, modes["exploration"])

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
    # TIMELINE (DATED) - Grade-aware
    # =========================
    def _build_timeline(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """Build timeline based on student's grade."""
        today = date.today()
        deadline = _parse_ouac_deadline(profile.grade)
        days_left = max(0, (deadline - today).days)
    
        if days_left > 365:
            return self._build_long_term_milestones(today, deadline, profile)
        else:
            return self._build_short_term_milestones(today, deadline, profile)

    def _build_short_term_milestones(self, today: date, deadline: date, profile: StudentProfile) -> List[Dict[str, Any]]:
        """Build milestones for students within 1 year of deadline (Grade 12)"""
        days_left = max(0, (deadline - today).days)
        
        def cap(d: date) -> date:
            return d if d <= deadline else deadline
    
        milestones = [
            (today, "Start Here", [
                "Confirm your top 6 Grade 12 U/M courses (and your prerequisites).",
                "Pick 6–10 programs (mix of safe/target/reach).",
            ]),
            (cap(today + timedelta(days=7)), "Within 7 Days", [
                "Save links + requirements for each shortlisted program.",
                "Start a simple tracker: program, prerequisites, admission notes, link.",
            ]),
            (cap(today + timedelta(days=21)), "Within 3 Weeks", [
                "Finalize your shortlist (aim 6–10).",
                "Identify any supplementary pieces (forms, interviews, portfolios) for each school.",
            ]),
            (deadline, f"OUAC Equal Consideration ({days_left} days left)", [
                "Submit applications for equal consideration (where applicable).",
                "Re-check each program page for updated requirements close to submit time.",
            ]),
        ]
    
        seen_dates = set()
        events: List[Dict[str, Any]] = []
        for d, title, items in milestones:
            ds = _iso(d)
            if ds in seen_dates:
                continue
            seen_dates.add(ds)
            events.append({"date": ds, "title": title, "items": items})
    
        return events

    def _build_long_term_milestones(self, today: date, deadline: date, profile: StudentProfile) -> List[Dict[str, Any]]:
        """Build milestones for students more than 1 year from deadline (Grade 9-11)"""
        days_left = max(0, (deadline - today).days)
        grade_lower = (profile.grade or "").lower()
        current_year = today.year
        
        events = []
        
        events.append({
            "date": _iso(today),
            "title": "Start Here",
            "items": [
                "Review your current course selections for next semester.",
                "Identify 2-3 broad interest areas to explore.",
                "Start tracking your extracurricular activities.",
            ]
        })
        
        three_months = today + timedelta(days=90)
        events.append({
            "date": _iso(three_months),
            "title": "3-Month Check-in",
            "items": [
                "Evaluate mid-term grades - identify subjects needing extra focus.",
                "Join or deepen involvement in 1-2 clubs/activities.",
                "Start a simple portfolio or achievements log.",
            ]
        })
        
        if today.month <= 6:
            end_of_year = date(current_year, 6, 30)
        else:
            end_of_year = date(current_year + 1, 6, 30)
        
        events.append({
            "date": _iso(end_of_year),
            "title": "End of School Year",
            "items": [
                "Review final grades - celebrate wins, note areas to improve.",
                "Plan summer activities: courses, jobs, volunteering, projects.",
                "Research programs loosely aligned with your interests.",
            ]
        })
        
        if "9" in grade_lower:
            events.append({
                "date": _iso(date(current_year + 1 if today.month >= 9 else current_year, 9, 1)),
                "title": "Grade 10 Start",
                "items": [
                    "Select courses strategically - keep STEM/humanities options open.",
                    "Deepen extracurricular involvement - aim for leadership.",
                    "Start building skills relevant to your interests.",
                ]
            })
            events.append({
                "date": _iso(date(current_year + 2 if today.month >= 9 else current_year + 1, 9, 1)),
                "title": "Grade 11 Start",
                "items": [
                    "Focus on prerequisite courses for target programs.",
                    "Begin serious portfolio/project work.",
                    "Research specific programs and admission requirements.",
                ]
            })
        elif "10" in grade_lower:
            events.append({
                "date": _iso(date(current_year + 1 if today.month >= 9 else current_year, 9, 1)),
                "title": "Grade 11 Start",
                "items": [
                    "Focus on prerequisite courses for target programs.",
                    "Begin serious portfolio/project work.",
                    "Research specific programs and admission requirements.",
                ]
            })
        
        grade_12_start = deadline - timedelta(days=150)
        events.append({
            "date": _iso(grade_12_start),
            "title": "Grade 12 Application Prep",
            "items": [
                "Finalize program shortlist (6-10 programs: safe/target/reach).",
                "Gather all requirements: transcripts, references, portfolios.",
                "Start supplementary application materials.",
            ]
        })
        
        events.append({
            "date": _iso(deadline),
            "title": f"OUAC Equal Consideration Deadline",
            "items": [
                "Submit all applications by this date for equal consideration.",
                "Ensure all supplementary materials are submitted.",
            ],
            "meta": {"days_left": days_left}
        })
        
        events.sort(key=lambda e: e["date"])
        return events

    # =========================
    # PROJECT CHECKLIST
    # =========================
    def _build_projects(self, profile: StudentProfile) -> List[Dict[str, Any]]:
        """Checklist tab = projects + proof-of-interest tasks."""
        interest = (profile.interests or "").lower()
        blocks: List[Dict[str, Any]] = []
    
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
        elif any(k in interest for k in ["computer", "software", "cs", "ai", "data"]):
            blocks.append({
                "title": "Build + Ship a Mini App (2–3 weeks)",
                "items": [
                    "Build one app (web tool, bot, data dashboard) related to your interest.",
                    "Write a README: problem, approach, features, screenshots, next steps.",
                    "Deploy or publish (GitHub + optional live demo link).",
                ],
            })
        elif any(k in interest for k in ["health", "bio", "medical", "life", "neuro"]):
            blocks.append({
                "title": "Research / Evidence Project (2–3 weeks)",
                "items": [
                    "Pick a topic + write a 1–2 page brief using credible sources.",
                    "Summarize: what's known, what's debated, and your conclusion.",
                    "Present it (club talk / poster / short video) and keep a linkable copy.",
                ],
            })
        else:
            blocks.append({
                "title": "Interest Portfolio (2–3 weeks)",
                "items": [
                    "Create one tangible artifact (case study, design, mini research brief, app).",
                    "Document: first version → feedback → improved version.",
                    "Publish somewhere linkable (Drive/Notion/GitHub).",
                ],
            })
    
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
    def _format_full_plan_safe(
        self,
        profile: StudentProfile,
        ui_programs: List[Dict[str, Any]],
        analysis: str,
        timeline_events: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
    ) -> str:
        """Format full plan with graceful fallback if LLM formatting fails."""
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

        try:
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
                "**Tip:** Always verify prerequisites/admission details using the program link.\n\n"
                f"DATA:\n{payload_json}"
            )

            out = self.llm.generate(prompt, system)
            if out and out.strip():
                return out.strip()
                
        except Exception as e:
            logger.warning(f"LLM formatting failed, using fallback: {e}")

        return self._format_full_plan_fallback(payload)

    def _format_full_plan_fallback(self, payload: Dict[str, Any]) -> str:
        """Deterministic markdown formatting when LLM unavailable."""
        p = payload["profile"]
        lines: List[str] = []

        lines.append("## ✨ Your Personalized University Roadmap\n")
        lines.append(f"**🎯 Interest:** {p.get('interest','')}  ")
        lines.append(f"**📊 Grade:** {p.get('grade','')} | **Average:** {p.get('average','')}%  ")
        subj = ", ".join((p.get("subjects") or [])[:6]) or "Not specified"
        lines.append(f"**📚 Subjects:** {subj}\n")
        lines.append("---\n")

        lines.append("## Top Matching Programs\n")
        lines.append("| Program | University | Match | Co-op | Prereqs |")
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
    # FOLLOWUP
    # =========================
    def followup(self, question: str, session: Session) -> ServiceResult:
        try:
            context = session.last_profile.to_context_string() if session.last_profile else ""
            prompt = self.prompts.followup_prompt(question, context)
            response = self.llm.generate(prompt, self.prompts.followup_system_prompt())
            return ServiceResult.success(message=response) if response else ServiceResult.failure("No response")
        except Exception as e:
            return ServiceResult.failure(str(e))