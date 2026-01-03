from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class ServiceResult:
    """Generic service result structure"""
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls, message: str = "", data: Optional[Dict[str, Any]] = None):
        return cls(ok=True, message=message, data=data)

    @classmethod
    def failure(cls, message: str):
        return cls(ok=False, message=message, data=None)


@dataclass
class StudentProfile:
    """Validated student profile"""
    name: str
    grade: str
    average: float
    interests: str
    subjects: List[str]
    extracurriculars: str
    location: str

    # New: student constraints/preferences (optional)
    preferences: List[str] = field(default_factory=list)
    preferences_free_text: str = ""

    def to_context_string(self) -> str:
        prefs_parts: List[str] = []
        if self.preferences:
            prefs_parts.append(", ".join(self.preferences))
        if (self.preferences_free_text or "").strip():
            prefs_parts.append(self.preferences_free_text.strip())
        prefs = " | ".join(prefs_parts) if prefs_parts else "None"

        return f"""Name: {self.name}
Grade: {self.grade}
Average: {self.average}%
Interests: {self.interests}
Subjects: {', '.join(self.subjects)}
Extracurriculars: {self.extracurriculars}
Location: {self.location}
Preferences: {prefs}"""
