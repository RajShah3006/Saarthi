# controllers.py - Thin handlers that delegate to services

import logging
import traceback
import json
import re
from typing import Tuple, List, Any

import gradio as gr

from config import Config
from models import StudentProfile
from services.session import SessionManager
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from services.llm_client import LLMClient
from utils.validators import Validators

logger = logging.getLogger("saarthi.controllers")


DATA_MARKER_RE = re.compile(r"<!--SAARTHI_DATA:(.+?)-->", re.DOTALL)


class Controllers:
    """Thin controller layer - validates input, calls services, formats output"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize services
        self.session_manager = SessionManager(config)
        self.llm_client = LLMClient(config)
        self.program_search = ProgramSearchService(config)
        self.roadmap_service = RoadmapService(config, self.llm_client, self.program_search)

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
                welcome_message,            # Output display (Full Plan tab)
                session.id                  # Session state
            )

        except Exception as e:
            logger.error(f"Start session error: {e}\n{traceback.format_exc()}")
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                f"❌ Error starting session: {str(e)}",
                ""
            )

    @staticmethod
    def _minimize_program(p: dict) -> dict:
        """
        Remove huge fields like embeddings and keep only UI-relevant fields.
        This prevents massive HTML comment payloads and keeps rendering fast.
        """
        if not isinstance(p, dict):
            return {}

        keep = {
            "program_name": p.get("program_name") or p.get("name") or p.get("program"),
            "program_url": p.get("program_url") or p.get("url") or p.get("link") or p.get("program_page"),
            "university": p.get("university") or p.get("school") or p.get("institution"),

            # scoring keys (if your pipeline provides them)
            "match_percent": p.get("match_percent") or p.get("match") or p.get("score"),

            "admission_average": p.get("admission_average") or p.get("admission") or p.get("admission_req"),
            "prerequisites": p.get("prerequisites") or p.get("prereqs") or p.get("required_courses"),

            "missing": p.get("missing") or p.get("missing_prereqs") or p.get("missing_courses"),
            "coop_available": p.get("coop_available") or p.get("coop"),
        }

        # Drop empties
        return {k: v for k, v in keep.items() if v not in (None, "", [], {})}


    @staticmethod
    def _build_marker(profile: StudentProfile, programs: List[dict]) -> str:
        # Convert profile to plain dict safely
        try:
            profile_dict = profile.model_dump()  # pydantic
        except Exception:
            profile_dict = getattr(profile, "__dict__", {})

        payload = {
            "profile": profile_dict,
            "programs": programs,
        }
        # Keep marker compact (no embeddings)
        return f"<!--SAARTHI_DATA:{json.dumps(payload, ensure_ascii=False)}-->"

    def handle_generate_roadmap(
        self,
        subjects: List[str],
        interests: str,
        extracurriculars: str,
        average: float,
        grade: str,
        location: str,
        budget: str,
        session_id: str
    ) -> str:
        """Generate university roadmap - main feature"""
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                return "⚠️ Session expired. Please refresh the page to start a new session."

            validation = Validators.validate_profile_inputs(
                interests=interests,
                extracurriculars=extracurriculars,
                average=average,
                grade=grade,
                location=location,
                config=self.config
            )
            if not validation.ok:
                return f"⚠️ **Validation Error**\n\n{validation.message}"

            profile = StudentProfile(
                name=session.name,
                grade=grade,
                average=float(average),
                interests=Validators.sanitize_text(interests, self.config.MAX_INTERESTS_LENGTH),
                subjects=subjects or [],
                extracurriculars=Validators.sanitize_text(extracurriculars, self.config.MAX_INTERESTS_LENGTH),
                location=Validators.sanitize_text(location, self.config.MAX_LOCATION_LENGTH),
                budget=budget
            )

            result = self.roadmap_service.generate(profile, session)
            if not result.ok:
                return f"❌ **Error**\n\n{result.message}\n\n*Error ID: {result.error_id}*"

            # Update session context for follow-ups
            session.last_profile = profile
            raw_programs = (result.data or {}).get("programs", [])
            session.last_programs = raw_programs
            session.conversation_summary = f"Generated roadmap for {profile.interests}"

            # Minimize programs (remove embeddings)
            min_programs = [self._minimize_program(p) for p in raw_programs]
            marker = self._build_marker(profile, min_programs)

            # IMPORTANT: append the marker so UI can render Programs tab correctly
            return f"{result.message}\n\n{marker}"

        except Exception as e:
            error_id = str(hash(str(e)))[:8]
            logger.error(f"Generate roadmap error [{error_id}]: {e}\n{traceback.format_exc()}")
            return (
                "❌ **Unexpected Error**\n\n"
                "Something went wrong. Please try again.\n\n"
                f"*Error ID: {error_id}*"
            )

    def handle_followup(self, question: str, current_output: str, session_id: str) -> Tuple[str, str]:
        """Handle follow-up questions with context"""
        try:
            if not question or not question.strip():
                return "", current_output

            session = self.session_manager.get_session(session_id)
            if not session:
                return "", current_output + "\n\n⚠️ Session expired. Please refresh to continue."

            question = Validators.sanitize_text(question, self.config.MAX_FOLLOWUP_LENGTH)

            # Preserve embedded marker, but keep it out of visible text changes
            marker = ""
            m = DATA_MARKER_RE.search(current_output or "")
            if m:
                marker = m.group(0)
                base_output = DATA_MARKER_RE.sub("", current_output).strip()
            else:
                base_output = current_output or ""

            result = self.roadmap_service.followup(question, session)
            if not result.ok:
                new_text = base_output + f"\n\n❌ {result.message}"
                if marker:
                    new_text = f"{new_text}\n\n{marker}"
                return "", new_text

            # Append Q&A but keep marker at end
            new_output = f"{base_output}\n\n---\n\n**You:** {question}\n\n**Saarthi:** {result.message}"
            if marker:
                new_output = f"{new_output}\n\n{marker}"

            return "", new_output

        except Exception as e:
            logger.error(f"Followup error: {e}\n{traceback.format_exc()}")
            return "", (current_output or "") + f"\n\n❌ Error processing question: {str(e)}"

    def handle_clear_form(self) -> Tuple:
        """Clear form inputs"""
        return (
            [],         # subjects
            "",         # interests
            "",         # extracurriculars
            85,         # average (default)
            "Grade 12", # grade (default)
            "",         # location
            "None"      # budget (default)
        )