# controllers.py
import logging
import traceback
from typing import Tuple, List, Any, Dict

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
    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SessionManager(config)
        self.llm_client = LLMClient(config)
        self.program_search = ProgramSearchService(config)
        self.roadmap_service = RoadmapService(config, self.llm_client, self.program_search)

    def handle_start_session(self, name: str) -> Tuple[Any, Any, str, str]:
        try:
            name = Validators.sanitize_text(name, max_length=50) or "Student"
            session = self.session_manager.create_session(name)

            logger.info(f"Session started: {session.id} for {name}")

            welcome_message = f"""## Welcome, {name}!
Fill in your profile below and click **Generate Roadmap** to get personalized university guidance.

**Tips for best results:**
- Be specific about your interests
- Include all relevant subjects
- Mention anything important in preferences (optional)

*Session ID: {session.id[:8]}...*
"""

            # reset structured session state
            session.last_plan_md = welcome_message
            session.last_ui_programs = []
            session.last_phases = []
            session.last_profile_ui = {}

            return (
                gr.update(visible=False),
                gr.update(visible=True),
                welcome_message,
                session.id,
            )

        except Exception as e:
            logger.error(f"Start session error: {e}\n{traceback.format_exc()}")
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                f"❌ Error starting session: {str(e)}",
                "",
            )

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
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                msg = "⚠️ Session expired. Please refresh the page to start a new session."
                return {"md": msg, "programs": [], "phases": [], "profile": {}}

            validation = Validators.validate_profile_inputs(
                interests=interests,
                extracurriculars=extracurriculars,
                average=average,
                grade=grade,
                location=location,
                config=self.config,
            )
            if not validation.ok:
                msg = f"⚠️ **Validation Error**\n\n{validation.message}"
                return {"md": msg, "programs": [], "phases": [], "profile": {}}

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
                msg = f"❌ **Error**\n\n{result.message}\n\n*Error ID: {result.error_id}*"
                return {"md": msg, "programs": [], "phases": [], "profile": {}}

            session.last_profile = profile

            ui_programs = (result.data or {}).get("programs", []) or []
            ui_phases = (result.data or {}).get("phases", []) or []
            ui_profile = {
                "interest": profile.interests,
                "grade": profile.grade,
                "avg": profile.average,
                "subjects": ", ".join(profile.subjects[:5]) if profile.subjects else "",
            }

            session.last_ui_programs = ui_programs
            session.last_phases = ui_phases
            session.last_profile_ui = ui_profile
            session.last_plan_md = result.message

            return {
                "md": result.message,
                "programs": ui_programs,
                "phases": ui_phases,
                "profile": ui_profile,
            }

        except Exception as e:
            error_id = str(hash(str(e)))[:8]
            logger.error(f"Generate roadmap error [{error_id}]: {e}\n{traceback.format_exc()}")
            msg = (
                "❌ **Unexpected Error**\n\n"
                "Something went wrong. Please try again.\n\n"
                f"*Error ID: {error_id}*"
            )
            return {"md": msg, "programs": [], "phases": [], "profile": {}}

    def handle_followup(self, question: str, session_id: str) -> Dict[str, Any]:
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                msg = "⚠️ Session expired. Please refresh to continue."
                return {"md": msg, "programs": [], "phases": [], "profile": {}}

            question = (question or "").strip()
            if not question:
                # just re-render last plan
                return {
                    "md": session.last_plan_md or "",
                    "programs": session.last_ui_programs or [],
                    "phases": session.last_phases or [],
                    "profile": session.last_profile_ui or {},
                }

            question = Validators.sanitize_text(question, self.config.MAX_FOLLOWUP_LENGTH)

            result = self.roadmap_service.followup(question, session)
            if not result.ok:
                session.last_plan_md = (session.last_plan_md or "") + f"\n\n❌ {result.message}"
            else:
                base = session.last_plan_md or ""
                session.last_plan_md = f"{base}\n\n---\n\n**You:** {question}\n\n**Saarthi:** {result.message}"

            return {
                "md": session.last_plan_md,
                "programs": session.last_ui_programs or [],
                "phases": session.last_phases or [],
                "profile": session.last_profile_ui or {},
            }

        except Exception as e:
            logger.error(f"Followup error: {e}\n{traceback.format_exc()}")
            msg = (session.last_plan_md if session else "") + f"\n\n❌ Error processing question: {str(e)}"
            return {"md": msg, "programs": [], "phases": [], "profile": {}}

    def handle_clear_form(self) -> Tuple:
        return (
            [],
            [],
            "",
            "",
            85,
            "Grade 12",
            "",
            "",
        )
