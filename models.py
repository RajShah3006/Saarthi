# models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ServiceResult:
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None

    @staticmethod
    def success(data: Any) -> "ServiceResult":
        return ServiceResult(ok=True, data=data, error=None)

    @staticmethod
    def failure(error: str) -> "ServiceResult":
        return ServiceResult(ok=False, data=None, error=error)


@dataclass
class Program:
    name: str
    url: str
    prerequisites: str
    admission_average: str
    match_percent: float = 0.0
    match_reasons: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Program":
        return Program(
            name=d.get("program_name", ""),
            url=d.get("program_url", ""),
            prerequisites=d.get("prerequisites", ""),
            admission_average=d.get("admission_average", ""),
            match_percent=float(d.get("match_percent", 0.0) or 0.0),
            match_reasons=d.get("match_reasons", []) or [],
        )

    def to_min_dict(self) -> Dict[str, Any]:
        return {
            "program_name": self.name,
            "program_url": self.url,
            "prerequisites": self.prerequisites,
            "admission_average": self.admission_average,
            "match_percent": float(self.match_percent or 0.0),
            "match_reasons": self.match_reasons or [],
        }


@dataclass
class StudentProfile:
    name: str
    grade: str
    average: float
    interests: str
    subjects: List[str]
    extracurriculars: str
    location: str
    budget: str
    preferences: List[str] = field(default_factory=list)
    preferences_other: str = ""

    def to_context_string(self) -> str:
        subjects_str = ", ".join(self.subjects) if self.subjects else "Not specified"

        prefs = ", ".join(self.preferences) if self.preferences else "Not specified"
        if self.preferences_other:
            prefs = (prefs if prefs != "Not specified" else "") + (
                ", " if prefs not in ("", "Not specified") else ""
            ) + self.preferences_other

        return f"""- Name: {self.name}
- Grade: {self.grade}
- Average: {self.average}%
- Interests: {self.interests or 'Not specified'}
- Current Subjects: {subjects_str}
- Extracurriculars: {self.extracurriculars or 'Not specified'}
- Location: {self.location or 'Not specified'}
- Preferences: {prefs or 'Not specified'}"""
