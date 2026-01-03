# models.py - Domain models with validation
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class Program:
    """University program - matches your programs.json structure"""
    program_name: str
    program_url: str = ""
    prerequisites: str = ""
    admission_average: str = ""
    university_name: str = ""
    location: str = ""
    co_op_available: bool = False
    
    # For TF-IDF search
    search_text: str = field(default="", repr=False)
    
    # Embedding from your JSON (768 dimensions)
    embedding: List[float] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        # Build search text combining relevant fields
        parts = [
            self.program_name,
            self.prerequisites,
            self.university_name,
            self.location,
        ]
        self.search_text = " ".join(filter(None, parts)).lower()
        
        # Try to extract university name from program_url if not set
        if not self.university_name and self.program_url:
            self.university_name = self._extract_university_from_url(self.program_url)
    
    def _extract_university_from_url(self, url: str) -> str:
        """Extract university name from ouinfo URL"""
        # URL format: https://www.ouinfo.ca/programs/university-name/code
        try:
            if "ouinfo.ca/programs/" in url:
                parts = url.split("/programs/")[1].split("/")
                if parts:
                    uni_slug = parts[0]
                    # Map common slugs to full names
                    uni_map = {
                        "algoma": "Algoma University",
                        "brock": "Brock University",
                        "carleton": "Carleton University",
                        "guelph": "University of Guelph",
                        "lakehead": "Lakehead University",
                        "laurentian": "Laurentian University",
                        "mcmaster": "McMaster University",
                        "nipissing": "Nipissing University",
                        "ocad": "OCAD University",
                        "ontario-tech": "Ontario Tech University",
                        "ottawa": "University of Ottawa",
                        "queens": "Queen's University",
                        "toronto": "University of Toronto",
                        "toronto-metropolitan": "Toronto Metropolitan University",
                        "trent": "Trent University",
                        "waterloo": "University of Waterloo",
                        "western": "Western University",
                        "laurier": "Wilfrid Laurier University",
                        "windsor": "University of Windsor",
                        "york": "York University",
                        "uoit": "Ontario Tech University",
                    }
                    return uni_map.get(uni_slug, uni_slug.replace("-", " ").title())
        except:
            pass
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding computed fields)"""
        return {
            "program_name": self.program_name,
            "program_url": self.program_url,
            "prerequisites": self.prerequisites,
            "admission_average": self.admission_average,
            "university_name": self.university_name,
            "location": self.location,
            "co_op_available": self.co_op_available,
            # Don't include embedding or search_text - too large
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Program":
        """Create Program from your JSON structure"""
        # Extract embedding separately
        embedding = data.get("embedding", [])
        
        # Check for co-op in program name or prerequisites
        program_name = data.get("program_name", "")
        prereqs = data.get("prerequisites", "")
        has_coop = "co-op" in program_name.lower() or "coop" in program_name.lower()
        
        # Create program
        program = cls(
            program_name=program_name,
            program_url=data.get("program_url", ""),
            prerequisites=prereqs,
            admission_average=data.get("admission_average", ""),
            university_name=data.get("university_name", ""),
            location=data.get("location", ""),
            co_op_available=has_coop,
        )
        
        # Set embedding after creation
        program.embedding = embedding if isinstance(embedding, list) else []
        
        return program


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
    preferences: str  # <-- replaced budget

    def to_context_string(self) -> str:
        """Format for prompt context"""
        subjects_str = ", ".join(self.subjects) if self.subjects else "None specified"
        prefs_str = self.preferences.strip() if self.preferences else "Not specified"

        return f"""- Name: {self.name}
- Grade: {self.grade}
- Average: {self.average}%
- Interests: {self.interests or 'Not specified'}
- Current Subjects: {subjects_str}
- Extracurriculars: {self.extracurriculars or 'Not specified'}
- Location: {self.location or 'Not specified'}
- Preferences: {prefs_str}"""


@dataclass
class Session:
    """User session (in-memory only, no persistence)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Student"
    created_at: datetime = field(default_factory=datetime.now)
    last_profile: Optional[StudentProfile] = None
    last_programs: List[Program] = field(default_factory=list)
    conversation_summary: str = ""
    
    def is_valid(self, timeout_minutes: int) -> bool:
        """Check if session is still valid"""
        elapsed = (datetime.now() - self.created_at).total_seconds() / 60
        return elapsed < timeout_minutes


@dataclass
class ServiceResult:
    """Consistent result wrapper for all service calls"""
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_id: Optional[str] = None
    
    @classmethod
    def success(cls, message: str, data: Dict = None) -> "ServiceResult":
        return cls(ok=True, message=message, data=data)
    
    @classmethod
    def failure(cls, message: str, error_id: str = None) -> "ServiceResult":
        return cls(ok=False, message=message, error_id=error_id or str(uuid.uuid4())[:8])