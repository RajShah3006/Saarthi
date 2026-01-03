# controllers.py
from typing import Any, Dict, List, Optional, Tuple

from config import Config
from models import ServiceResult, StudentProfile
from services.session import SessionManager
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from utils.validators import Validators


class Controllers:
    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SessionManager()
        self.program_search = ProgramSearchService(config=config)
        self.roadmap_service = RoadmapService(config=config)

    def handle_generate_roadmap(
        self,
        subjects: List[str],
        interests: str,
        extracurriculars: str,
        average: float,
        grade: str,
        location: str,
        preferences: List[str],
        preferences_other: str,
        session_id: str,
    ) -> ServiceResult:
        # Validate profile inputs (existing validator — minimal change)
        ok, error = Validators.validate_profile(
            subjects=subjects,
            interests=interests,
            extracurriculars=extracurriculars,
            average=average,
            grade=grade,
            location=location,
            config=self.config,
        )
        if not ok:
            return ServiceResult.failure(error)

        # Build profile
        profile = StudentProfile(
            name="Student",
            grade=grade,
            average=float(average),
            interests=interests.strip(),
            subjects=subjects or [],
            extracurriculars=extracurriculars.strip(),
            location=location.strip() if location else "",
            budget="None",  # budget section removed from UI
            preferences=preferences or [],
            preferences_other=(preferences_other or "").strip(),
        )

        # Save session details
        self.session_manager.update_profile(session_id=session_id, profile=profile)

        # Program search
        programs = self.program_search.search_with_profile(profile)

        # Roadmap generation (LLM)
        roadmap_bundle = self.roadmap_service.generate(profile=profile, programs=programs)

        return ServiceResult.success(roadmap_bundle)

    def handle_clear_form(self) -> Tuple:
        """Clear form inputs"""
        return (
            [],         # subjects
            "",         # interests
            "",         # extracurriculars
            85,         # average (default)
            "Grade 12", # grade (default)
            "",         # location
            [],         # preferences (default)
            "",         # other preferences (default)
        )
