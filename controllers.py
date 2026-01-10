# controllers.py - Thin handlers that delegate to services (DICT plan output)

import logging
import traceback
from typing import Tuple, Any, Dict, List

import gradio as gr

from config import Config
from models import StudentProfile
from services.session import SessionManager
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from services.llm_client import LLMClient
from utils.validators import Validators

logger = logging.getLogger("saarthi.controllers")


class Controllers:
    """Thin controller layer - validates input, calls services, returns structured plan dict"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize services
        self.session_manager = SessionManager(config)
        self.llm_client = LLMClient(config)
        self.program_search = ProgramSearchService(config)
        self.roadmap_service = RoadmapService(config, self.llm_client, self.program_search)

    # -------------------------------------------------------
    # LOGIN
    # -------------------------------------------------------
    def handle_start_session(self, name: str) -> Tuple[Any, Any, str, str]:
        """Start a new session (no auth, just session tracking)"""
        try:
            name = Validators.sanitize_text(name, max_length=50) or "Student"
            session = self.session_manager.create_session(name)

            logger.info(f"Session started: {session.id} for {name}")

            welcome_message = f"""## Welcome, {name}!
Fill in your profile below and click **Generate Roadmap** to get personalized university guidance.
**Tips for best results:**
- Be specific about your interests
- Include all relevant subjects
- Mention your extracurricular activities
*Session ID: {session.id[:8]}...*
"""
            return (
                gr.update(visible=False),   # Hide login
                gr.update(visible=True),    # Show student dashboard
                welcome_message,            # Markdown to show in Full Plan when outputs view opens
                session.id,                 # Session state
            )

        except Exception as e:
            logger.error(f"Start session error: {e}\n{traceback.format_exc()}")
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                f"❌ Error starting session: {str(e)}",
                "",
            )

    # -------------------------------------------------------
    # ROADMAP GENERATION (returns DICT plan)
    # -------------------------------------------------------
    def handle_generate_roadmap(
        self,
        subjects: List[str],
        interests: str,
        extracurriculars: str,
        average: float,
        grade: str,
        location: str,
        preferences: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Returns a plan dict:
        {
          "md": "...",
          "profile": {...},
          "programs": [...],
          "timeline_events": [...],
          "projects": [...]
        }
        """
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                return {
                    "md": "⚠️ Session expired. Please refresh the page to start a new session.",
                    "profile": {},
                    "programs": [],
                    "timeline_events": [],
                    "projects": [],
                }

            validation = Validators.validate_profile_inputs(
                interests=interests,
                extracurriculars=extracurriculars,
                average=average,
                grade=grade,
                location=location,
                config=self.config,
            )
            if not validation.ok:
                return {
                    "md": f"⚠️ **Validation Error**\n\n{validation.message}",
                    "profile": {},
                    "programs": [],
                    "timeline_events": [],
                    "projects": [],
                }

            profile = StudentProfile(
                name=session.name,
                grade=grade,
                average=float(average),
                interests=Validators.sanitize_text(interests, self.config.MAX_INTERESTS_LENGTH),
                subjects=subjects or [],
                extracurriculars=Validators.sanitize_text(extracurriculars, self.config.MAX_INTERESTS_LENGTH),
                location=Validators.sanitize_text(location, self.config.MAX_LOCATION_LENGTH),
                preferences=Validators.sanitize_text(preferences, self.config.MAX_INTERESTS_LENGTH),
            )

            result = self.roadmap_service.generate(profile, session)
            if not result.ok:
                return {
                    "md": f"❌ **Error**\n\n{result.message}\n\n*Error ID: {result.error_id}*",
                    "profile": {},
                    "programs": [],
                    "timeline_events": [],
                    "projects": [],
                }

            # Store session context
            session.last_profile = profile

            # ✅ FIX: Use correct keys from roadmap.py
            ui_programs = (result.data or {}).get("programs", []) or []
            timeline_events = (result.data or {}).get("timeline_events", []) or []
            projects = (result.data or {}).get("projects", []) or []

            # Store for followup rendering
            session.last_ui_programs = ui_programs
            session.last_timeline_events = timeline_events  # Add as dynamic attr
            session.last_projects = projects  # Add as dynamic attr
            session.last_plan_md = result.message or ""

            ui_profile = {
                "interest": profile.interests,
                "grade": profile.grade,
                "avg": profile.average,
                "subjects": ", ".join(profile.subjects[:5]) if profile.subjects else "",
                "location": profile.location or "",
                "preferences": profile.preferences or "",
                "extracurriculars": profile.extracurriculars or "",
            }

            # ✅ FIX: Return correct keys that app.py expects
            return {
                "md": result.message or "",
                "profile": ui_profile,
                "programs": ui_programs,
                "timeline_events": timeline_events,
                "projects": projects,
            }

        except Exception as e:
            error_id = str(hash(str(e)))[:8]
            logger.error(f"Generate roadmap error [{error_id}]: {e}\n{traceback.format_exc()}")
            return {
                "md": (
                    "❌ **Unexpected Error**\n\n"
                    "Something went wrong. Please try again.\n\n"
                    f"*Error ID: {error_id}*"
                ),
                "profile": {},
                "programs": [],
                "timeline_events": [],
                "projects": [],
            }

    # -------------------------------------------------------
    # FOLLOWUP
    # ✅ FIX: Return tuple (cleared_question, new_md) as app.py expects
    # -------------------------------------------------------
    def handle_followup(self, question: str, current_md: str, session_id: str) -> Tuple[str, str]:
        """
        Returns (cleared_question, new_markdown)
        """
        try:
            base_md = (current_md or "").strip()

            if not question or not question.strip():
                return ("", base_md)

            session = self.session_manager.get_session(session_id)
            if not session:
                return ("", base_md + "\n\n⚠️ Session expired. Please refresh to continue.")

            q = Validators.sanitize_text(question, self.config.MAX_FOLLOWUP_LENGTH)

            result = self.roadmap_service.followup(q, session)
            if not result.ok:
                return ("", base_md + f"\n\n❌ {result.message}")

            # Append Q&A
            if "## Q&A" in base_md:
                new_md = base_md + f"\n\n**You:** {q}\n\n**Saarthi:** {result.message}\n"
            else:
                new_md = base_md + f"\n\n---\n\n## Q&A\n\n**You:** {q}\n\n**Saarthi:** {result.message}\n"

            # Update session cache
            session.last_plan_md = new_md

            return ("", new_md)  # ✅ Return tuple: (cleared_question, new_md)

        except Exception as e:
            logger.error(f"Followup error: {e}\n{traceback.format_exc()}")
            return ("", (current_md or "") + f"\n\n❌ Error processing question: {str(e)}")

    # -------------------------------------------------------
    # CLEAR FORM
    # -------------------------------------------------------
    def handle_clear_form(self) -> Tuple:
        return (
            [],         # subjects
            [],         # interest tags
            "",         # interest details
            "",         # extracurriculars
            85,         # average (default)
            "Grade 12", # grade (default)
            "",         # location
            "",         # preferences
        )

    # -------------------------------------------------------
    # Session helpers
    # -------------------------------------------------------
    def _session_programs(self, session_id: str) -> List[dict]:
        session = self.session_manager.get_session(session_id)
        if not session:
            return []
        return getattr(session, "last_ui_programs", []) or []

    def _session_timeline_events(self, session_id: str) -> List[dict]:
        session = self.session_manager.get_session(session_id)
        if not session:
            return []
        return getattr(session, "last_timeline_events", []) or []

    def _session_projects(self, session_id: str) -> List[dict]:
        session = self.session_manager.get_session(session_id)
        if not session:
            return []
        return getattr(session, "last_projects", []) or []

    def _session_profile(self, session_id: str) -> Dict[str, Any]:
        session = self.session_manager.get_session(session_id)
        if not session or not session.last_profile:
            return {}
        p = session.last_profile
        return {
            "interest": p.interests,
            "grade": p.grade,
            "avg": p.average,
            "subjects": ", ".join(p.subjects[:5]) if p.subjects else "",
            "location": p.location or "",
            "preferences": p.preferences or "",
            "extracurriculars": p.extracurriculars or "",
        }