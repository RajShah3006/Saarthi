# controllers.py - Controller layer for UI events

import json
import logging
from typing import Dict, Any, List, Tuple

from models import StudentProfile
from session import SessionManager
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from validators import validate_profile_inputs

logger = logging.getLogger("saarthi.controllers")


class Controllers:
    def __init__(
        self,
        session_manager: SessionManager,
        program_search: ProgramSearchService,
        roadmap_service: RoadmapService
    ):
        self.session_manager = session_manager
        self.program_search = program_search
        self.roadmap_service = roadmap_service

    @staticmethod
    def _minimize_program(program: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal program representation for UI embedding"""
        keep_fields = [
            "program_name",
            "university_name",
            "program_url",
            "admission_average",
            "prerequisites",
            "co_op_available",
            "match_percent",
            "missing_prereqs",
            "grade_assessment",
            "metrics",
        ]
        return {k: program.get(k) for k in keep_fields if k in program}

    @staticmethod
    def _build_marker(profile: StudentProfile, programs: List[dict]) -> str:
        """
        Embed JSON payload inside an HTML comment so it won't render,
        but we can parse it later for cleaner UI rendering.
        """

        # Convert profile to dict safely
        try:
            profile_dict = profile.model_dump()  # pydantic (if ever)
        except Exception:
            profile_dict = profile.__dict__

        def _json_default(o):
            # Handle numpy float32 / int64 etc
            try:
                import numpy as np  # type: ignore
                if isinstance(o, (np.integer, np.floating)):
                    return o.item()
            except Exception:
                pass
            # Fallback: stringify unknowns rather than crashing
            return str(o)

        payload = {
            "profile": profile_dict,
            "programs": programs,
        }

        return f"<!--SAARTHI_DATA:{json.dumps(payload, ensure_ascii=False, default=_json_default)}-->"

    def handle_generate_roadmap(
        self,
        subjects: List[str],
        interests: str,
        extracurriculars: str,
        average: float,
        grade: str,
        location: str,
        preferences: List[str],
        preferences_free_text: str,
        session_id: str,
    ) -> Tuple[str, str, str]:
        """
        Generate roadmap output.
        Returns: (status_text, roadmap_markdown_with_marker, session_id)
        """
        try:
            # Ensure session exists
            session = self.session_manager.get_or_create_session(session_id)

            # Validate
            errors = validate_profile_inputs(subjects, interests, extracurriculars, average, grade, location)
            if errors:
                return ("⚠️ " + " ".join(errors), "", session.session_id)

            # Build profile (Preferences are now first-class)
            profile = StudentProfile(
                name=session.name or "Student",
                grade=grade,
                average=float(average),
                interests=interests.strip(),
                subjects=subjects,
                extracurriculars=extracurriculars.strip(),
                location=(location or "").strip(),
                preferences=preferences or [],
                preferences_free_text=(preferences_free_text or "").strip(),
            )
            session.last_profile = profile
            logger.info(f"Session started: {session.session_id} for {profile.name}")

            # Generate roadmap
            result = self.roadmap_service.generate(profile, session)

            if not result.ok:
                return (f"❌ {result.message}", "", session.session_id)

            message = result.message or ""
            raw_programs = (result.data or {}).get("programs", [])

            # Minimize and embed
            min_programs = [self._minimize_program(p) for p in raw_programs if isinstance(p, dict)]
            marker = self._build_marker(profile, min_programs)

            return ("✅ Roadmap generated", message + "\n\n" + marker, session.session_id)

        except Exception as e:
            logger.exception("Error generating roadmap")
            return (f"❌ Error: {str(e)}", "", session_id)

    def handle_clear_form(self) -> Tuple:
        """Clear form inputs"""
        return (
            [],         # subjects
            "",         # interests
            "",         # extracurriculars
            85,         # average (default)
            "Grade 12", # grade (default)
            "",         # location
            [],         # preferences
            "",         # preferences free text
        )
