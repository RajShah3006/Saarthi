# models.py - Core data models

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Program:
    program_name: str
    program_url: str
    prerequisites: str
    admission_average: str
    embedding: Optional[List[float]] = None

    # Optional extra fields used internally
    university: str = ""
    match_score: float = 0.0
    relevance: float = 0.0
    embedding_score: float = 0.0
    grade_fit: float = 0.0
    prereq_fit: float = 0.0
    location_fit: float = 0.0
    co_op: bool = False
    missing_courses: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_minimal_dict(self) -> Dict[str, Any]:
        d = {
            "program_name": self.program_name,
            "program_url": self.program_url,
            "prerequisites": self.prerequisites,
            "admission_average": self.admission_average,
            "university": self.university,
            "match_score": float(self.match_score),
            "grade_fit": float(self.grade_fit),
            "prereq_fit": float(self.prereq_fit),
            "location_fit": float(self.location_fit),
            "co_op": bool(self.co_op),
            "missing_courses": list(self.missing_courses),
        }
        return d


@dataclass
class StudentProfile:
    name: str = "Student"
    interests: str = ""
    grade: str = "Grade 12"
    average: float = 85.0
    subjects: List[str] = field(default_factory=list)
    location: str = "Ontario"
    budget: str = "None"

    def __str__(self) -> str:
        return f"""Student Profile:
- Name: {self.name}
- Interests: {self.interests}
- Grade: {self.grade}
- Average: {self.average}%
- Subjects: {', '.join(self.subjects) if self.subjects else 'None'}
- Location: {self.location}
- Budget: {self.budget}"""


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Student"
    created_at: datetime = field(default_factory=datetime.now)
    last_profile: Optional[StudentProfile] = None
    last_results: List[Program] = field(default_factory=list)

    def is_valid(self, minutes: int = 60) -> bool:
        return (datetime.now() - self.created_at).total_seconds() < minutes * 60


@dataclass
class ServiceResult:
    ok: bool
    message: str = ""
    data: Any = None
