'''
# services/program_search.py - Smarter Mathematical Ranking
import json
import logging
import math
import re
from typing import List, Tuple, Dict, Any, Optional

import numpy as np

from config import Config
from models import Program, StudentProfile

logger = logging.getLogger("saarthi.search")


class ProgramSearchService:
    """
    Smarter ranking that:
    1. Penalizes irrelevant programs (Sport Management for robotics interest)
    2. Rewards direct keyword matches in program name
    3. Properly handles admission averages
    4. Cleans garbage from prerequisites
    """
    
    # Keywords for different fields - used for relevance filtering
    FIELD_KEYWORDS = {
        "robotics": ["robotics", "mechatronics", "automation", "mechanical", "electrical", "control", "embedded"],
        "automation": ["automation", "robotics", "mechatronics", "control systems", "plc", "industrial"],
        "engineering": ["engineering", "mechatronics", "mechanical", "electrical", "computer engineering", "systems"],
        "computer science": ["computer science", "computing", "software", "programming", "algorithms"],
        "ai": ["artificial intelligence", "machine learning", "ai", "data science", "neural"],
        "business": ["business", "commerce", "accounting", "finance", "marketing", "management"],
        "medicine": ["medicine", "health sciences", "nursing", "biology", "life sciences", "pre-med"],
        "law": ["law", "legal", "criminology", "justice"],
    }
    
    # Garbage strings to remove from prerequisites
    GARBAGE_STRINGS = [
        "about this website", "accessibility", "site map", "privacy statement",
        "contact", "email:", "site map,", "privacy statement,", "accessibility,",
    ]
    
    def __init__(self, config: Config):
        self.config = config
        self.programs: List[Program] = []
        self.has_embeddings = False
        self.embedding_matrix: Optional[np.ndarray] = None
        
        self._load_programs()
    
    def _load_programs(self):
        """Load and clean programs"""
        try:
            if not self.config.PROGRAMS_FILE.exists():
                logger.error(f"File not found: {self.config.PROGRAMS_FILE}")
                return
            
            with open(self.config.PROGRAMS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.programs = []
            embeddings = []
            
            for item in data:
                try:
                    program = Program.from_dict(item)
                    
                    # Clean the prerequisites
                    program.prerequisites = self._clean_prerequisites(program.prerequisites)
                    
                    self.programs.append(program)
                    
                    if program.embedding:
                        embeddings.append(program.embedding)
                    else:
                        embeddings.append(None)
                        
                except Exception as e:
                    pass
            
            # Build embedding matrix
            valid_emb = [e for e in embeddings if e]
            if valid_emb:
                self.has_embeddings = True
                emb_dim = len(valid_emb[0])
                self.embedding_matrix = np.zeros((len(self.programs), emb_dim))
                for i, emb in enumerate(embeddings):
                    if emb:
                        self.embedding_matrix[i] = emb
            
            logger.info(f"✅ Loaded {len(self.programs)} programs")
            
        except Exception as e:
            logger.error(f"Load error: {e}")
    
    def _clean_prerequisites(self, prereqs: str) -> str:
        """Remove garbage from prerequisites"""
        if not prereqs:
            return ""
        
        cleaned = prereqs.lower()
        for garbage in self.GARBAGE_STRINGS:
            cleaned = cleaned.replace(garbage, "")
        
        # Remove extra commas and whitespace
        cleaned = re.sub(r',\s*,', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(' ,')
        
        # Capitalize properly
        return cleaned.title() if cleaned else ""
    
    # ========== RELEVANCE SCORING ==========
    
    def _calculate_relevance_score(self, program: Program, interests: str) -> float:
        """
        Calculate how relevant this program is to user's interests.
        This is the KEY improvement - it penalizes irrelevant programs.
        """
        if not interests:
            return 0.5
        
        interests_lower = interests.lower()
        program_name_lower = program.program_name.lower()
        prereqs_lower = program.prerequisites.lower()
        
        score = 0.0
        max_score = 0.0
        
        # Extract what fields the user is interested in
        user_fields = []
        for field, keywords in self.FIELD_KEYWORDS.items():
            if any(kw in interests_lower for kw in keywords):
                user_fields.append(field)
        
        # If no specific field detected, use the raw interests
        if not user_fields:
            user_fields = [interests_lower]
        
        # Check if program name contains relevant keywords
        for field in user_fields:
            field_keywords = self.FIELD_KEYWORDS.get(field, [field])
            max_score += 1.0
            
            # Direct match in program name (most important)
            if any(kw in program_name_lower for kw in field_keywords):
                score += 1.0
            # Partial match in prerequisites
            elif any(kw in prereqs_lower for kw in field_keywords):
                score += 0.3
        
        # PENALTY: Check for clearly irrelevant programs
        irrelevant_for_stem = ["sport management", "communication", "commerce", 
                               "marketing", "hospitality", "tourism", "fashion",
                               "social work", "child studies", "recreation"]
        
        if any(irr in program_name_lower for irr in irrelevant_for_stem):
            # Check if user actually wants these
            wants_business = any(f in user_fields for f in ["business", "commerce", "marketing"])
            wants_social = any(f in user_fields for f in ["social work", "communication"])
            
            if not wants_business and not wants_social:
                score *= 0.1  # Heavy penalty
        
        # BONUS: Direct keyword match in program name
        interest_words = interests_lower.split()
        for word in interest_words:
            if len(word) > 3 and word in program_name_lower:
                score += 0.5
        
        # Normalize
        return min(1.0, score / max(max_score, 1.0))
    
    # ========== MATHEMATICAL SCORING ==========
    
    @staticmethod
    def _sigmoid(x: float, k: float = 0.3) -> float:
        try:
            return 1 / (1 + math.exp(-k * x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
    
    def _parse_admission_average(self, avg_str: str) -> Tuple[float, bool]:
        """
        Parse admission average. Returns (value, is_competitive).
        'Below 75%' means easy admission.
        '90-95%' means very competitive.
        """
        if not avg_str:
            return 75.0, False
        
        avg_str = avg_str.lower()
        
        # "Below 75%" or "under 75%"
        if "below" in avg_str or "under" in avg_str:
            match = re.search(r'(\d+)', avg_str)
            if match:
                return float(match.group(1)) - 5, False  # Easy admission
            return 70.0, False
        
        # Range "85-90%"
        range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', avg_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return (low + high) / 2, high > 85
        
        # Single number "85%"
        single = re.search(r'(\d+)', avg_str)
        if single:
            val = float(single.group(1))
            return val, val > 85
        
        # Text descriptions
        if "competitive" in avg_str or "high" in avg_str:
            return 90.0, True
        if "mid 80" in avg_str:
            return 85.0, True
        if "low 80" in avg_str:
            return 80.0, False
        
        return 75.0, False
    
    def _calculate_grade_score(self, student_avg: float, program: Program) -> Tuple[float, str]:
        """
        Calculate grade fit. Returns (score, assessment).
        """
        if student_avg <= 0:
            return 0.5, "Unknown"
        
        program_avg, is_competitive = self._parse_admission_average(program.admission_average)
        delta = student_avg - program_avg
        
        # Calculate base score using sigmoid
        score = self._sigmoid(delta, k=0.25)
        
        # Assessment
        if delta >= 10:
            assessment = "Safe"
        elif delta >= 5:
            assessment = "Good"
        elif delta >= 0:
            assessment = "Target"
        elif delta >= -5:
            assessment = "Reach"
        else:
            assessment = "Long Shot"
        
        # Bonus for competitive programs where student qualifies
        if is_competitive and delta >= 0:
            score = min(1.0, score * 1.1)
        
        return score, assessment
    
    def _calculate_prerequisite_score(self, student_subjects: List[str], program: Program) -> Tuple[float, List[str]]:
        """
        Check prerequisites. Returns (score, missing_courses).
        """
        if not program.prerequisites:
            return 0.8, []
        if not student_subjects:
            return 0.5, []
        
        prereqs = program.prerequisites.lower()
        subjects_str = " ".join(student_subjects).lower()
        
        # Course patterns to check
        course_patterns = [
            ("MCV4U", ["mcv4u", "calculus", "vectors"]),
            ("MHF4U", ["mhf4u", "advanced functions"]),
            ("ENG4U", ["eng4u", "english"]),
            ("SBI4U", ["sbi4u", "biology"]),
            ("SCH4U", ["sch4u", "chemistry"]),
            ("SPH4U", ["sph4u", "physics"]),
            ("MDM4U", ["mdm4u", "data management"]),
            ("ICS4U", ["ics4u", "computer science"]),
        ]
        
        required = []
        missing = []
        
        for course_name, keywords in course_patterns:
            if any(kw in prereqs for kw in keywords):
                required.append(course_name)
                if not any(kw in subjects_str for kw in keywords):
                    missing.append(course_name)
        
        if not required:
            return 0.8, []
        
        score = (len(required) - len(missing)) / len(required)
        return score, missing
    
    def _calculate_location_score(self, student_loc: str, program: Program) -> Optional[float]:
        """Location score - None if not specified"""
        if not student_loc or not student_loc.strip():
            return None
        
        program_loc = (program.location or program.university_name or "").lower()
        student_loc = student_loc.lower().strip()
        
        if not program_loc:
            return 0.5
        
        # Direct match
        if student_loc in program_loc or program_loc in student_loc:
            return 1.0
        
        # GTA
        gta = ["toronto", "mississauga", "brampton", "markham", "vaughan", "scarborough", "gta", "york"]
        if any(c in student_loc for c in gta) and any(c in program_loc for c in gta):
            return 0.85
        
        # Ontario
        if "ontario" in student_loc or "on" in student_loc:
            return 0.6
        
        return 0.3
    
    # ========== EMBEDDING SEARCH ==========
    
    def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get embedding from Gemini"""
        try:
            import google.generativeai as genai
            
            if not self.config.GEMINI_API_KEY:
                return None
            
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=query[:2000],
                task_type="retrieval_query",
            )
            return np.array(response["embedding"])
            
        except Exception as e:
            logger.warning(f"Embedding error: {e}")
            return None
    
    def _calculate_embedding_scores(self, query: str) -> np.ndarray:
        """Calculate embedding similarity"""
        scores = np.zeros(len(self.programs))
        
        if not query or not self.has_embeddings:
            return scores
        
        query_emb = self._get_query_embedding(query)
        if query_emb is None:
            return scores
        
        # Normalize query
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)
        
        # Calculate similarity for each program
        for i in range(len(self.programs)):
            prog_emb = self.embedding_matrix[i]
            if np.linalg.norm(prog_emb) > 0:
                prog_norm = prog_emb / (np.linalg.norm(prog_emb) + 1e-8)
                scores[i] = max(0, np.dot(query_norm, prog_norm))
        
        # Normalize
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return scores
    
    # ========== COMBINED SCORING ==========
    
    def _calculate_final_score(
        self,
        program: Program,
        profile: StudentProfile,
        embedding_score: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Smart combined scoring with:
        - Relevance filtering (most important!)
        - Embedding similarity
        - Grade fit
        - Prerequisite match
        - Location (conditional)
        """
        
        # 1. RELEVANCE (Critical - filters out irrelevant programs)
        relevance = self._calculate_relevance_score(program, profile.interests)
        
        # 2. Grade fit
        grade_score, grade_assessment = self._calculate_grade_score(profile.average, program)
        
        # 3. Prerequisites
        prereq_score, missing_prereqs = self._calculate_prerequisite_score(profile.subjects, program)
        
        # 4. Location (conditional)
        location_score = self._calculate_location_score(profile.location, program)
        
        # === WEIGHT ASSIGNMENT ===
        # Relevance is now the dominant factor
        w_relevance = 0.35
        w_embedding = 0.25
        w_grade = 0.20
        w_prereq = 0.15
        w_location = 0.05
        
        # If location not specified, redistribute
        if location_score is None:
            location_score = 0.0
            w_relevance += 0.03
            w_embedding += 0.02
            w_location = 0.0
        
        # If no subjects, reduce prereq weight
        if not profile.subjects:
            w_relevance += w_prereq * 0.5
            w_embedding += w_prereq * 0.5
            w_prereq = 0.0
        
        # Normalize weights
        total = w_relevance + w_embedding + w_grade + w_prereq + w_location
        w_relevance /= total
        w_embedding /= total
        w_grade /= total
        w_prereq /= total
        w_location /= total
        
        # === FINAL SCORE ===
        final = (
            w_relevance * relevance +
            w_embedding * embedding_score +
            w_grade * grade_score +
            w_prereq * prereq_score +
            w_location * location_score
        )
        
        # Apply relevance as a multiplier too (double penalty for irrelevant)
        if relevance < 0.3:
            final *= relevance
        
        breakdown = {
            "relevance": round(relevance, 3),
            "embedding": round(embedding_score, 3),
            "grade": round(grade_score, 3),
            "grade_assessment": grade_assessment,
            "prereq": round(prereq_score, 3),
            "missing_prereqs": missing_prereqs,
            "location": round(location_score, 3) if profile.location else "N/A",
            "final": round(final, 3),
        }
        
        return final, breakdown
    
    # ========== PUBLIC API ==========
    
    def search_with_profile(
        self, 
        profile: StudentProfile, 
        top_k: int = None
    ) -> List[Tuple[Program, float, Dict]]:
        """Main search with smart ranking"""
        top_k = top_k or self.config.TOP_K_PROGRAMS
        
        if not self.programs:
            return []
        
        # Get embedding scores
        query = f"{profile.interests} {profile.extracurriculars}".strip()
        embedding_scores = self._calculate_embedding_scores(query)
        
        # Calculate final scores
        results = []
        for i, program in enumerate(self.programs):
            final, breakdown = self._calculate_final_score(
                program, profile, embedding_scores[i]
            )
            results.append((program, final, breakdown))
        
        # Sort by final score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Log top results
        logger.info(f"\n{'='*60}")
        logger.info(f"SEARCH: {profile.interests[:40]}...")
        for i, (p, s, b) in enumerate(results[:5], 1):
            logger.info(f"{i}. [{b['final']:.2f}] {p.program_name[:35]} @ {p.university_name}")
            logger.info(f"   Rel={b['relevance']:.2f} Emb={b['embedding']:.2f} Grd={b['grade']:.2f}({b['grade_assessment']}) Pre={b['prereq']:.2f}")
        logger.info(f"{'='*60}\n")
        
        return results[:top_k]
    
    def get_top_programs_with_profile(self, profile: StudentProfile, top_k: int = None) -> List[Program]:
        results = self.search_with_profile(profile, top_k)
        return [p for p, _, _ in results]
'''
# services/program_search.py - Enhanced Mathematical Ranking Engine
# Version 3.0 - Fixed relevance detection, typo tolerance, better filtering

import json
import logging
import math
import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass, field

import numpy as np

from config import Config
from models import Program, StudentProfile

logger = logging.getLogger("saarthi.search")


@dataclass
class ScoringWeights:
    """Configurable scoring weights"""
    relevance: float = 0.35
    embedding: float = 0.25
    grade: float = 0.20
    prereq: float = 0.15
    location: float = 0.05
    
    def normalize(self) -> 'ScoringWeights':
        """Normalize weights to sum to 1.0"""
        total = self.relevance + self.embedding + self.grade + self.prereq + self.location
        if total > 0:
            return ScoringWeights(
                relevance=self.relevance / total,
                embedding=self.embedding / total,
                grade=self.grade / total,
                prereq=self.prereq / total,
                location=self.location / total
            )
        return self


@dataclass 
class ScoreBreakdown:
    """Detailed breakdown of program score"""
    relevance: float = 0.0
    embedding: float = 0.0
    grade: float = 0.0
    grade_assessment: str = "Unknown"
    prereq: float = 0.0
    missing_prereqs: List[str] = field(default_factory=list)
    location: float = 0.0
    location_specified: bool = False
    final: float = 0.0
    penalties_applied: List[str] = field(default_factory=list)
    bonuses_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relevance": round(self.relevance, 3),
            "embedding": round(self.embedding, 3),
            "grade": round(self.grade, 3),
            "grade_assessment": self.grade_assessment,
            "prereq": round(self.prereq, 3),
            "missing_prereqs": self.missing_prereqs,
            "location": round(self.location, 3) if self.location_specified else "N/A",
            "final": round(self.final, 3),
            "penalties": self.penalties_applied,
            "bonuses": self.bonuses_applied,
        }


class ProgramSearchService:
    """
    Enhanced ranking engine v3.0 that:
    1. Penalizes irrelevant programs (Sport Management for robotics interest)
    2. Rewards direct keyword matches in program name
    3. Properly handles admission averages with sigmoid scoring
    4. Cleans garbage from prerequisites
    5. Supports semantic search via embeddings
    6. Caches expensive operations for performance
    7. Provides detailed score breakdowns for transparency
    8. NEW: Typo tolerance via fuzzy matching
    9. NEW: Filters out zero-relevance programs
    10. NEW: Better keyword coverage (space, computers, etc.)
    """
    
    # ==================== FIELD KEYWORDS ====================
    # Expanded keyword mappings for better field detection
    FIELD_KEYWORDS: Dict[str, List[str]] = {
        # STEM Fields
        "robotics": [
            "robotics", "mechatronics", "automation", "mechanical", "electrical", 
            "control", "embedded", "robot", "autonomous", "actuator", "sensor"
        ],
        "automation": [
            "automation", "robotics", "mechatronics", "control systems", "plc", 
            "industrial", "manufacturing", "process control", "scada"
        ],
        "mechanical": [
            "mechanical", "mechanical engineering", "mechatronics", "machines",
            "thermodynamics", "fluid", "dynamics", "manufacturing", "automotive",
            "vehicle", "engine", "mechanics"
        ],
        "engineering": [
            "engineering", "mechatronics", "mechanical", "electrical", "civil",
            "computer engineering", "systems", "aerospace", "biomedical", "chemical",
            "industrial", "structural", "materials"
        ],
        "computer science": [
            "computer science", "computing", "software", "programming", "algorithms",
            "data structures", "systems", "developer", "coder", "comp sci", "cs",
            "computer", "computers", "computational", "informatics"
        ],
        "computers": [
            "computer", "computers", "computing", "computer science", "computer engineering",
            "software", "hardware", "programming", "it", "information technology",
            "tech", "technology", "digital"
        ],
        "ai": [
            "artificial intelligence", "machine learning", "ai", "data science", 
            "neural", "deep learning", "nlp", "computer vision", "ml", "analytics"
        ],
        "cybersecurity": [
            "cybersecurity", "security", "infosec", "ethical hacking", "penetration",
            "cryptography", "network security", "cyber"
        ],
        "mathematics": [
            "mathematics", "math", "statistics", "actuarial", "applied math",
            "pure math", "computational", "quantitative"
        ],
        
        # Space & Aerospace - NEW!
        "space": [
            "space", "aerospace", "astronaut", "astrophysics", "astronomy",
            "satellite", "rocket", "spacecraft", "aviation", "aeronautical",
            "aerodynamics", "cosmos", "planetary", "nasa", "orbital"
        ],
        "aerospace": [
            "aerospace", "aeronautical", "aviation", "aircraft", "flight",
            "aerospace engineering", "space", "rocket", "propulsion", "avionics"
        ],
        "physics": [
            "physics", "astrophysics", "quantum", "particle", "nuclear",
            "theoretical", "applied physics", "optics", "mechanics", "relativity"
        ],
        
        # Business Fields
        "business": [
            "business", "commerce", "accounting", "finance", "marketing", 
            "management", "entrepreneurship", "bba", "mba", "administration"
        ],
        "economics": [
            "economics", "economy", "economic", "finance", "banking",
            "monetary", "fiscal", "microeconomics", "macroeconomics"
        ],
        
        # Health & Life Sciences
        "medicine": [
            "medicine", "health sciences", "nursing", "biology", "life sciences", 
            "pre-med", "medical", "physician", "doctor", "healthcare", "clinical"
        ],
        "psychology": [
            "psychology", "psych", "mental health", "counseling", "behavioral",
            "cognitive", "neuroscience", "therapy"
        ],
        "pharmacy": [
            "pharmacy", "pharmacology", "pharmaceutical", "drug", "pharmacist"
        ],
        
        # Arts & Humanities
        "arts": [
            "arts", "fine arts", "visual arts", "studio arts", "creative",
            "design", "graphic", "illustration", "animation"
        ],
        "music": [
            "music", "musical", "composition", "performance", "orchestra",
            "band", "vocal", "instrumental"
        ],
        "literature": [
            "literature", "english", "writing", "creative writing", "journalism",
            "communications", "media", "publishing"
        ],
        
        # Social Sciences
        "law": [
            "law", "legal", "criminology", "justice", "paralegal", "lawyer",
            "attorney", "jurisprudence", "pre-law"
        ],
        "social work": [
            "social work", "community", "human services", "welfare", "advocacy",
            "nonprofit", "social justice"
        ],
        "political science": [
            "political science", "politics", "government", "international relations",
            "public policy", "diplomacy", "public administration"
        ],
        
        # Environmental
        "environmental": [
            "environmental", "sustainability", "ecology", "climate", "conservation",
            "renewable", "green", "earth science", "geography"
        ],
        
        # Architecture & Design
        "architecture": [
            "architecture", "architectural", "urban planning", "interior design",
            "landscape", "building", "construction"
        ],
    }
    
    # Common typos and their corrections
    TYPO_CORRECTIONS: Dict[str, str] = {
        "mechanicel": "mechanical",
        "mechanicle": "mechanical",
        "mechanial": "mechanical",
        "machanical": "mechanical",
        "computor": "computer",
        "compter": "computer",
        "computar": "computer",
        "programing": "programming",
        "enginneering": "engineering",
        "enginnering": "engineering",
        "enginering": "engineering",
        "engineerng": "engineering",
        "engeneering": "engineering",
        "robtics": "robotics",
        "robotcs": "robotics",
        "aersospace": "aerospace",
        "areospace": "aerospace",
        "astronmy": "astronomy",
        "phyiscs": "physics",
        "physcs": "physics",
        "scince": "science",
        "sciense": "science",
        "sofware": "software",
        "softare": "software",
        "tecnology": "technology",
        "tecnolgy": "technology",
        "buisness": "business",
        "bussiness": "business",
        "busines": "business",
        "finace": "finance",
        "finanse": "finance",
        "acounting": "accounting",
        "accountng": "accounting",
        "mathmatics": "mathematics",
        "mathemtics": "mathematics",
        "biologoy": "biology",
        "chemisty": "chemistry",
        "chemestry": "chemistry",
    }
    
    # Programs to penalize for STEM students
    IRRELEVANT_FOR_STEM: List[str] = [
        "sport management", "sports management", "recreation management",
        "hospitality", "tourism", "fashion", "culinary",
        "child studies", "early childhood", "family studies",
        "liberal arts", "general arts", "undeclared",
    ]
    
    # Programs to penalize for non-STEM students
    IRRELEVANT_FOR_NON_STEM: List[str] = [
        "mechatronics", "robotics engineering", "computer engineering",
        "electrical engineering", "mechanical engineering",
    ]
    
    # Garbage strings to remove from prerequisites
    GARBAGE_STRINGS: List[str] = [
        "about this website", "accessibility", "site map", "privacy statement",
        "contact", "email:", "site map,", "privacy statement,", "accessibility,",
        "click here", "learn more", "visit website", "apply now", "register",
        "copyright", "all rights reserved", "terms of use", "cookie policy",
    ]
    
    # Ontario course code patterns (Grade 12 University level)
    COURSE_PATTERNS: List[Tuple[str, List[str]]] = [
        # Math
        ("MCV4U", ["mcv4u", "calculus", "vectors", "calculus and vectors"]),
        ("MHF4U", ["mhf4u", "advanced functions", "advanced function"]),
        ("MDM4U", ["mdm4u", "data management", "statistics"]),
        
        # Sciences
        ("SBI4U", ["sbi4u", "biology", "bio"]),
        ("SCH4U", ["sch4u", "chemistry", "chem"]),
        ("SPH4U", ["sph4u", "physics", "phys"]),
        ("SES4U", ["ses4u", "earth science", "earth and space"]),
        
        # English & Languages
        ("ENG4U", ["eng4u", "english", "grade 12 english"]),
        ("FRA4U", ["fra4u", "french", "français"]),
        
        # Computer Science
        ("ICS4U", ["ics4u", "computer science", "programming", "comp sci"]),
        ("TEJ4M", ["tej4m", "computer engineering", "tech"]),
        
        # Business
        ("BBB4M", ["bbb4m", "business", "international business"]),
        ("BAF3M", ["baf3m", "accounting", "financial accounting"]),
        
        # Arts
        ("AVI4M", ["avi4m", "visual arts", "art"]),
        ("AMU4M", ["amu4m", "music"]),
    ]
    
    # GTA cities for location matching
    GTA_CITIES: List[str] = [
        "toronto", "mississauga", "brampton", "markham", "vaughan", 
        "scarborough", "north york", "etobicoke", "richmond hill",
        "oakville", "burlington", "hamilton", "oshawa", "pickering",
        "ajax", "whitby", "newmarket", "aurora", "gta", "york region"
    ]
    
    # Other Ontario regions
    ONTARIO_REGIONS: Dict[str, List[str]] = {
        "southwestern": ["london", "windsor", "kitchener", "waterloo", "guelph", "cambridge"],
        "eastern": ["ottawa", "kingston", "belleville", "cornwall"],
        "northern": ["sudbury", "thunder bay", "north bay", "sault ste marie"],
        "central": ["barrie", "orillia", "peterborough", "lindsay"],
    }
    
    # Minimum relevance threshold - programs below this are filtered out
    MIN_RELEVANCE_THRESHOLD: float = 0.1
    
    # Fuzzy matching threshold (0.0 to 1.0)
    FUZZY_MATCH_THRESHOLD: float = 0.75
    
    def __init__(self, config: Config):
        self.config = config
        self.programs: List[Program] = []
        self.has_embeddings: bool = False
        self.embedding_matrix: Optional[np.ndarray] = None
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        self._load_programs()
    
    # ==================== TYPO CORRECTION & FUZZY MATCHING ====================
    
    def _correct_typos(self, text: str) -> str:
        """Fix common typos in user input"""
        if not text:
            return text
        
        words = text.lower().split()
        corrected_words = []
        
        for word in words:
            # Direct typo correction
            if word in self.TYPO_CORRECTIONS:
                corrected_words.append(self.TYPO_CORRECTIONS[word])
                logger.debug(f"Typo corrected: '{word}' -> '{self.TYPO_CORRECTIONS[word]}'")
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words)
    
    def _fuzzy_match(self, word: str, target: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)"""
        if not word or not target:
            return 0.0
        return SequenceMatcher(None, word.lower(), target.lower()).ratio()
    
    def _find_best_field_match(self, word: str) -> Tuple[Optional[str], float]:
        """
        Find the best matching field for a word using fuzzy matching.
        Returns (field_name, confidence) or (None, 0.0)
        """
        if len(word) < 3:
            return None, 0.0
        
        best_field = None
        best_score = 0.0
        
        for field, keywords in self.FIELD_KEYWORDS.items():
            # Check direct match with field name
            score = self._fuzzy_match(word, field)
            if score > best_score:
                best_score = score
                best_field = field
            
            # Check keywords
            for keyword in keywords:
                score = self._fuzzy_match(word, keyword)
                if score > best_score:
                    best_score = score
                    best_field = field
        
        if best_score >= self.FUZZY_MATCH_THRESHOLD:
            return best_field, best_score
        
        return None, 0.0
    
    # ==================== DATA LOADING ====================
    
    def _load_programs(self) -> None:
        """Load and clean programs from JSON file"""
        try:
            if not self.config.PROGRAMS_FILE or not self.config.PROGRAMS_FILE.exists():
                logger.error(f"Programs file not found: {self.config.PROGRAMS_FILE}")
                return
            
            with open(self.config.PROGRAMS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.programs = []
            embeddings: List[Optional[List[float]]] = []
            
            for item in data:
                try:
                    program = Program.from_dict(item)
                    
                    # Clean the prerequisites
                    program.prerequisites = self._clean_prerequisites(program.prerequisites)
                    
                    self.programs.append(program)
                    embeddings.append(program.embedding if program.embedding else None)
                        
                except Exception as e:
                    logger.debug(f"Skipped invalid program entry: {e}")
            
            # Build embedding matrix for vectorized operations
            self._build_embedding_matrix(embeddings)
            
            logger.info(f"✅ Loaded {len(self.programs)} programs "
                       f"({'with' if self.has_embeddings else 'without'} embeddings)")
            
        except Exception as e:
            logger.error(f"Failed to load programs: {e}")
    
    def _build_embedding_matrix(self, embeddings: List[Optional[List[float]]]) -> None:
        """Build numpy matrix from embeddings for fast similarity computation"""
        valid_embeddings = [e for e in embeddings if e is not None]
        
        if not valid_embeddings:
            self.has_embeddings = False
            return
        
        self.has_embeddings = True
        emb_dim = len(valid_embeddings[0])
        self.embedding_matrix = np.zeros((len(self.programs), emb_dim), dtype=np.float32)
        
        for i, emb in enumerate(embeddings):
            if emb is not None:
                self.embedding_matrix[i] = np.array(emb, dtype=np.float32)
        
        # Pre-normalize all program embeddings
        norms = np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1)  # Avoid division by zero
        self.embedding_matrix = self.embedding_matrix / norms
        
        logger.debug(f"Built embedding matrix: {self.embedding_matrix.shape}")
    
    def _clean_prerequisites(self, prereqs: str) -> str:
        """Remove garbage strings and normalize prerequisite text"""
        if not prereqs:
            return ""
        
        cleaned = prereqs.lower()
        
        # Remove garbage strings
        for garbage in self.GARBAGE_STRINGS:
            cleaned = cleaned.replace(garbage.lower(), "")
        
        # Remove URLs
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r'www\.\S+', '', cleaned)
        
        # Remove email addresses
        cleaned = re.sub(r'\S+@\S+', '', cleaned)
        
        # Remove extra punctuation and whitespace
        cleaned = re.sub(r'[,;]{2,}', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(' ,;.')
        
        # Title case for readability
        return cleaned.title() if cleaned else ""
    
    # ==================== RELEVANCE SCORING ====================
    
    def _detect_user_fields(self, interests: str) -> Tuple[List[str], bool, str]:
        """
        Detect which academic fields the user is interested in.
        Returns (list of fields, is_stem_focused, corrected_interests)
        
        Now includes:
        - Typo correction
        - Fuzzy matching for misspelled words
        """
        if not interests:
            return [], False, ""
        
        # Step 1: Correct known typos
        corrected_interests = self._correct_typos(interests)
        interests_lower = corrected_interests.lower()
        
        detected_fields: Set[str] = set()
        
        # Step 2: Direct keyword matching
        for field, keywords in self.FIELD_KEYWORDS.items():
            if any(kw in interests_lower for kw in keywords):
                detected_fields.add(field)
        
        # Step 3: Fuzzy matching for words that didn't match directly
        words = interests_lower.split()
        for word in words:
            if len(word) < 3:
                continue
            
            # Skip if we already matched this word
            already_matched = False
            for field in detected_fields:
                keywords = self.FIELD_KEYWORDS.get(field, [])
                if any(kw in word or word in kw for kw in keywords):
                    already_matched = True
                    break
            
            if not already_matched:
                # Try fuzzy matching
                matched_field, confidence = self._find_best_field_match(word)
                if matched_field:
                    detected_fields.add(matched_field)
                    logger.info(f"Fuzzy matched '{word}' -> field '{matched_field}' (confidence: {confidence:.2f})")
        
        # Log detected fields
        if detected_fields:
            logger.info(f"Detected fields for '{interests[:50]}...': {detected_fields}")
        else:
            logger.warning(f"No fields detected for interests: '{interests[:50]}...'")
        
        # Determine if STEM-focused
        stem_fields = {
            "robotics", "automation", "mechanical", "engineering", "computer science",
            "computers", "ai", "cybersecurity", "mathematics", "medicine", "pharmacy",
            "space", "aerospace", "physics"
        }
        is_stem = bool(detected_fields & stem_fields)
        
        return list(detected_fields), is_stem, corrected_interests
    
    def _calculate_relevance_score(
        self, 
        program: Program, 
        interests: str,
        user_fields: List[str],
        is_stem: bool,
        corrected_interests: str = ""
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate how relevant this program is to user's interests.
        Returns (score, penalties_applied, bonuses_applied)
        
        Key improvement: Uses corrected interests and fuzzy matching
        """
        if not interests and not user_fields:
            return 0.5, [], []
        
        penalties: List[str] = []
        bonuses: List[str] = []
        
        # Use corrected interests if available
        search_text = (corrected_interests or interests).lower()
        program_name_lower = program.program_name.lower()
        prereqs_lower = program.prerequisites.lower()
        
        score = 0.0
        max_score = 0.0
        
        # If no specific field detected, try fuzzy matching on program name
        if not user_fields:
            # Fallback: check if any interest word fuzzy-matches the program
            for word in search_text.split():
                if len(word) > 3:
                    if self._fuzzy_match(word, program_name_lower) > 0.6:
                        score += 0.5
                        bonuses.append(f"Fuzzy match: '{word}'")
            max_score = 1.0
        else:
            # Check keyword matches for each detected field
            for field in user_fields:
                field_keywords = self.FIELD_KEYWORDS.get(field, [field])
                max_score += 1.0
                
                matched = False
                
                # Direct match in program name (most important - 1.0 points)
                for kw in field_keywords:
                    if kw in program_name_lower:
                        score += 1.0
                        bonuses.append(f"Program name contains '{kw}' (field: {field})")
                        matched = True
                        break
                
                if not matched:
                    # Fuzzy match in program name (0.7 points)
                    for kw in field_keywords:
                        if len(kw) > 3 and self._fuzzy_match(kw, program_name_lower) > 0.7:
                            score += 0.7
                            bonuses.append(f"Program name fuzzy-matches '{kw}'")
                            matched = True
                            break
                
                if not matched:
                    # Match in prerequisites (0.3 points)
                    for kw in field_keywords:
                        if kw in prereqs_lower:
                            score += 0.3
                            bonuses.append(f"Prerequisites mention '{kw}'")
                            matched = True
                            break
        
        # MAJOR PENALTY: Business/irrelevant programs for STEM students
        if is_stem:
            for irr in self.IRRELEVANT_FOR_STEM:
                if irr in program_name_lower:
                    score *= 0.05  # 95% penalty!
                    penalties.append(f"'{irr}' is irrelevant for STEM interests")
                    break
        
        # PENALTY: Technical programs for non-STEM students
        if not is_stem and user_fields:
            wants_tech = any(f in user_fields for f in [
                "engineering", "robotics", "computer science", "computers",
                "mechanical", "aerospace", "space", "physics"
            ])
            if not wants_tech:
                for irr in self.IRRELEVANT_FOR_NON_STEM:
                    if irr in program_name_lower:
                        score *= 0.2
                        penalties.append(f"Technical program for non-technical interests")
                        break
        
        # BONUS: Direct keyword match in program name (from original interests)
        interest_words = [w for w in search_text.split() if len(w) > 3]
        stop_words = {'want', 'like', 'love', 'interested', 'study', 'learn', 'about', 'with', 'and', 'the'}
        for word in interest_words:
            if word not in stop_words and word in program_name_lower:
                score += 0.5
                bonuses.append(f"Direct word match: '{word}'")
        
        # BONUS: Co-op programs for STEM students
        if program.co_op_available and is_stem:
            score += 0.2
            bonuses.append("Co-op available (valuable for STEM)")
        
        # BONUS: Program name contains interest-related words via fuzzy match
        for word in interest_words:
            if word not in stop_words and len(word) > 4:
                # Check if word fuzzy-matches any part of program name
                name_words = program_name_lower.split()
                for name_word in name_words:
                    if self._fuzzy_match(word, name_word) > 0.8:
                        score += 0.3
                        bonuses.append(f"Strong fuzzy match: '{word}' ~ '{name_word}'")
                        break
        
        # Normalize score
        final_score = min(1.0, score / max(max_score, 1.0)) if max_score > 0 else 0.0
        
        return final_score, penalties, bonuses
    
    # ==================== GRADE SCORING ====================
    
    @staticmethod
    def _sigmoid(x: float, k: float = 0.25) -> float:
        """Smooth sigmoid function for grade scoring"""
        try:
            return 1.0 / (1.0 + math.exp(-k * x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
    
    def _parse_admission_average(self, avg_str: str) -> Tuple[float, bool]:
        """
        Parse admission average string to numeric value.
        Returns (average, is_competitive)
        
        Examples:
            "Below 75%" -> (70.0, False)
            "85-90%" -> (87.5, True)
            "Mid 80s" -> (85.0, True)
            "Competitive" -> (90.0, True)
        """
        if not avg_str:
            return 75.0, False
        
        avg_str = avg_str.lower().strip()
        
        # "Below X%" or "Under X%"
        below_match = re.search(r'(?:below|under)\s*(\d+)', avg_str)
        if below_match:
            return float(below_match.group(1)) - 5, False
        
        # Range "X-Y%" or "X–Y%"
        range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)', avg_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return (low + high) / 2, high >= 85
        
        # Single percentage "X%"
        single_match = re.search(r'(\d+(?:\.\d+)?)\s*%?', avg_str)
        if single_match:
            val = float(single_match.group(1))
            if val > 0:  # Sanity check
                return val, val >= 85
        
        # Text descriptions
        text_mappings = {
            "highly competitive": (92.0, True),
            "very competitive": (90.0, True),
            "competitive": (88.0, True),
            "high 80": (88.0, True),
            "mid 80": (85.0, True),
            "low 80": (82.0, False),
            "high 70": (78.0, False),
            "mid 70": (75.0, False),
            "low 70": (72.0, False),
        }
        
        for pattern, (value, competitive) in text_mappings.items():
            if pattern in avg_str:
                return value, competitive
        
        return 75.0, False
    
    def _calculate_grade_score(
        self, 
        student_avg: float, 
        program: Program
    ) -> Tuple[float, str]:
        """
        Calculate how well student's grades fit the program.
        Returns (score, assessment_label)
        
        Assessment labels:
            Safe:      delta >= +10 (very likely admission)
            Good:      delta >= +5  (strong chance)
            Target:    delta >= 0   (competitive chance)
            Reach:     delta >= -5  (possible but challenging)
            Long Shot: delta < -5   (unlikely but not impossible)
        """
        if student_avg <= 0:
            return 0.5, "Unknown"
        
        program_avg, is_competitive = self._parse_admission_average(program.admission_average)
        delta = student_avg - program_avg
        
        # Sigmoid-based score
        score = self._sigmoid(delta, k=0.25)
        
        # Assessment label
        if delta >= 10:
            assessment = "Safe"
        elif delta >= 5:
            assessment = "Good"
        elif delta >= 0:
            assessment = "Target"
        elif delta >= -5:
            assessment = "Reach"
        else:
            assessment = "Long Shot"
        
        # Bonus for competitive programs where student qualifies
        if is_competitive and delta >= 0:
            score = min(1.0, score * 1.1)
        
        # Small penalty for being way overqualified (might be bored)
        if delta > 20:
            score *= 0.95
        
        return score, assessment
    
    # ==================== PREREQUISITE SCORING ====================
    
    def _calculate_prerequisite_score(
        self, 
        student_subjects: List[str], 
        program: Program
    ) -> Tuple[float, List[str]]:
        """
        Check if student has required prerequisites.
        Returns (score, list of missing courses)
        """
        if not program.prerequisites:
            return 0.8, []  # No prereqs = easy admission
        
        if not student_subjects:
            return 0.5, []  # Unknown
        
        prereqs_lower = program.prerequisites.lower()
        subjects_str = " ".join(student_subjects).lower()
        
        required: List[str] = []
        missing: List[str] = []
        
        for course_code, keywords in self.COURSE_PATTERNS:
            # Check if this course is required
            if any(kw in prereqs_lower for kw in keywords):
                required.append(course_code)
                
                # Check if student has it
                if not any(kw in subjects_str for kw in keywords):
                    missing.append(course_code)
        
        if not required:
            return 0.8, []  # No specific requirements detected
        
        # Score based on how many requirements are met
        met = len(required) - len(missing)
        score = met / len(required)
        
        # Bonus if all requirements met
        if not missing:
            score = min(1.0, score * 1.1)
        
        return score, missing
    
    # ==================== LOCATION SCORING ====================
    
    def _calculate_location_score(
        self, 
        student_loc: str, 
        program: Program
    ) -> Optional[float]:
        """
        Calculate location preference score.
        Returns None if student didn't specify location preference.
        """
        if not student_loc or not student_loc.strip():
            return None
        
        program_loc = (program.location or program.university_name or "").lower()
        student_loc = student_loc.lower().strip()
        
        if not program_loc:
            return 0.5
        
        # Exact/direct match
        if student_loc in program_loc or program_loc in student_loc:
            return 1.0
        
        # GTA matching
        student_in_gta = any(city in student_loc for city in self.GTA_CITIES)
        program_in_gta = any(city in program_loc for city in self.GTA_CITIES)
        
        if student_in_gta and program_in_gta:
            return 0.85
        
        # Regional matching
        for region, cities in self.ONTARIO_REGIONS.items():
            student_in_region = any(city in student_loc for city in cities) or region in student_loc
            program_in_region = any(city in program_loc for city in cities)
            
            if student_in_region and program_in_region:
                return 0.75
        
        # General Ontario preference
        if "ontario" in student_loc or student_loc in ["on", "ont"]:
            return 0.6
        
        # Canada-wide
        if "canada" in student_loc:
            return 0.5
        
        return 0.3
    
    # ==================== EMBEDDING SEARCH ====================
    
    def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for search query using Gemini.
        Results are cached to avoid repeated API calls.
        """
        if not query:
            return None
        
        # Check cache first
        cache_key = query[:200]  # Truncate for cache key
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            import google.generativeai as genai
            
            if not self.config.GEMINI_API_KEY:
                return None
            
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=query[:2000],  # API limit
                task_type="retrieval_query",
            )
            
            embedding = np.array(response["embedding"], dtype=np.float32)
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            # Cache result
            self._embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None
    
    def _calculate_embedding_scores(self, query: str) -> np.ndarray:
        """
        Calculate cosine similarity between query and all program embeddings.
        Uses vectorized operations for efficiency.
        """
        scores = np.zeros(len(self.programs), dtype=np.float32)
        
        if not query or not self.has_embeddings:
            return scores
        
        query_emb = self._get_query_embedding(query)
        if query_emb is None:
            return scores
        
        # Vectorized cosine similarity (embeddings are pre-normalized)
        scores = np.dot(self.embedding_matrix, query_emb)
        scores = np.maximum(scores, 0)  # Clamp negative values
        
        # Normalize to 0-1 range
        max_score = scores.max()
        if max_score > 0:
            scores = scores / max_score
        
        return scores
    
    # ==================== COMBINED SCORING ====================
    
    def _calculate_final_score(
        self,
        program: Program,
        profile: StudentProfile,
        embedding_score: float,
        user_fields: List[str],
        is_stem: bool,
        corrected_interests: str = ""
    ) -> Tuple[float, ScoreBreakdown]:
        """
        Calculate final weighted score combining all factors.
        
        Scoring factors:
        - Relevance (35%): Keyword matching + field alignment
        - Embedding (25%): Semantic similarity via Gemini
        - Grade (20%): Sigmoid-based admission fit
        - Prerequisites (15%): Course requirement matching
        - Location (5%): Geographic preference
        
        Special rules:
        - Weights redistribute if location/subjects not provided
        - Double penalty applied if relevance < 0.3
        - Programs with relevance < MIN_RELEVANCE_THRESHOLD get zeroed
        """
        breakdown = ScoreBreakdown()
        
        # 1. Relevance score (now with corrected interests)
        relevance, penalties, bonuses = self._calculate_relevance_score(
            program, profile.interests, user_fields, is_stem, corrected_interests
        )
        breakdown.relevance = relevance
        breakdown.penalties_applied.extend(penalties)
        breakdown.bonuses_applied.extend(bonuses)
        
        # 2. Embedding score
        breakdown.embedding = embedding_score
        
        # 3. Grade score
        grade_score, grade_assessment = self._calculate_grade_score(profile.average, program)
        breakdown.grade = grade_score
        breakdown.grade_assessment = grade_assessment
        
        # 4. Prerequisite score
        prereq_score, missing = self._calculate_prerequisite_score(profile.subjects, program)
        breakdown.prereq = prereq_score
        breakdown.missing_prereqs = missing
        
        # 5. Location score
        location_score = self._calculate_location_score(profile.location, program)
        breakdown.location_specified = location_score is not None
        breakdown.location = location_score if location_score is not None else 0.0
        
        # Initialize weights
        weights = ScoringWeights()
        
        # Redistribute weights if location not specified
        if not breakdown.location_specified:
            weights.relevance += 0.03
            weights.embedding += 0.02
            weights.location = 0.0
        
        # Redistribute weights if no subjects provided
        if not profile.subjects:
            weights.relevance += weights.prereq * 0.5
            weights.embedding += weights.prereq * 0.5
            weights.prereq = 0.0
        
        # Normalize weights
        weights = weights.normalize()
        
        # Calculate weighted final score
        final = (
            weights.relevance * breakdown.relevance +
            weights.embedding * breakdown.embedding +
            weights.grade * breakdown.grade +
            weights.prereq * breakdown.prereq +
            weights.location * breakdown.location
        )
        
        # Double penalty for low relevance (filters out truly irrelevant programs)
        if breakdown.relevance < 0.3:
            final *= breakdown.relevance
            breakdown.penalties_applied.append(
                f"Low relevance penalty: ×{breakdown.relevance:.2f}"
            )
        
        breakdown.final = final
        
        return final, breakdown
    
    # ==================== PUBLIC API ====================
    
    def search_with_profile(
        self, 
        profile: StudentProfile, 
        top_k: Optional[int] = None
    ) -> List[Tuple[Program, float, Dict[str, Any]]]:
        """
        Main search method - finds best matching programs for a student.
        
        Args:
            profile: Student's profile with interests, grades, etc.
            top_k: Number of results to return (default from config)
        
        Returns:
            List of (Program, final_score, score_breakdown) tuples,
            sorted by final_score descending.
            
        NEW in v3.0:
        - Typo correction applied to interests
        - Low-relevance programs filtered out
        - Warning logged if no relevant programs found
        """
        top_k = top_k or self.config.TOP_K_PROGRAMS
        
        if not self.programs:
            logger.warning("No programs loaded")
            return []
        
        # Detect user's academic interests (with typo correction)
        user_fields, is_stem, corrected_interests = self._detect_user_fields(profile.interests)
        
        if corrected_interests != profile.interests.lower():
            logger.info(f"Typo correction: '{profile.interests}' -> '{corrected_interests}'")
        
        # Build search query from corrected interests + extracurriculars
        prefs = " ".join([p for p in (getattr(profile, "preferences", []) or []) if p])
        free = (getattr(profile, "preferences_free_text", "") or "").strip()
        if free:
            prefs = (prefs + " " if prefs else "") + free
        
        query = f"{corrected_interests} {profile.extracurriculars} {prefs}".strip()
        
        # Get embedding scores for all programs
        embedding_scores = self._calculate_embedding_scores(query)
        
        # Calculate final scores for each program
        all_results: List[Tuple[Program, float, Dict[str, Any]]] = []
        
        for i, program in enumerate(self.programs):
            final_score, breakdown = self._calculate_final_score(
                program=program,
                profile=profile,
                embedding_score=embedding_scores[i],
                user_fields=user_fields,
                is_stem=is_stem,
                corrected_interests=corrected_interests
            )
            match_percent = int(round(final_score * 100))

            breakdown_dict = breakdown.to_dict()
            breakdown_dict["match_percent"] = match_percent
            
            all_results.append((program, final_score, breakdown_dict))
        
        # Sort by final score descending
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        # Filter out programs with very low relevance
        relevant_results = [
            (prog, score, breakdown) 
            for prog, score, breakdown in all_results 
            if breakdown.get("relevance", 0) >= self.MIN_RELEVANCE_THRESHOLD
        ]
        
        # If no relevant results, log warning and return top by other metrics
        if not relevant_results:
            logger.warning(
                f"⚠️ No programs found matching interests: '{profile.interests}'. "
                f"Detected fields: {user_fields}. Returning top programs by other metrics."
            )
            # Return top results but mark them as low-relevance
            results = all_results[:top_k]
        else:
            results = relevant_results[:top_k]
            logger.info(f"Found {len(relevant_results)} relevant programs (showing top {len(results)})")
        
        # Log top results for debugging
        self._log_search_results(profile, results[:5], user_fields, corrected_interests)
        
        return results
    
    def _log_search_results(
        self, 
        profile: StudentProfile, 
        top_results: List[Tuple[Program, float, Dict]],
        user_fields: List[str] = None,
        corrected_interests: str = ""
    ) -> None:
        """Log search results for debugging"""
        logger.info(f"\n{'='*70}")
        logger.info(f"SEARCH: '{profile.interests[:50]}' | Avg: {profile.average}")
        if corrected_interests and corrected_interests != profile.interests.lower():
            logger.info(f"CORRECTED: '{corrected_interests[:50]}'")
        if user_fields:
            logger.info(f"DETECTED FIELDS: {user_fields}")
        logger.info(f"{'='*70}")
        
        if not top_results:
            logger.warning("No results to display!")
            return
        
        for i, (program, score, breakdown) in enumerate(top_results, 1):
            relevance = breakdown.get('relevance', 0)
            relevance_indicator = "✅" if relevance > 0.5 else ("⚠️" if relevance > 0.1 else "❌")
            
            logger.info(
                f"{i}. {relevance_indicator} [{breakdown.get('final', 0):.3f}] {program.program_name[:40]}"
                f" @ {program.university_name[:20]}"
            )
            logger.info(
                f"   Rel={relevance:.2f} "
                f"Emb={breakdown.get('embedding', 0):.2f} "
                f"Grd={breakdown.get('grade', 0):.2f}({breakdown.get('grade_assessment', '?')}) "
                f"Pre={breakdown.get('prereq', 0):.2f} "
                f"Loc={breakdown.get('location', 'N/A')}"
            )
            if breakdown.get('penalties'):
                logger.info(f"   ⚠️  Penalties: {', '.join(breakdown['penalties'][:3])}")
            if breakdown.get('bonuses'):
                logger.info(f"   ✅ Bonuses: {', '.join(breakdown['bonuses'][:3])}")
        
        logger.info(f"{'='*70}\n")
    
    def get_top_programs(
        self, 
        profile: StudentProfile, 
        top_k: Optional[int] = None
    ) -> List[Program]:
        """
        Convenience method - returns just the Program objects.
        
        Args:
            profile: Student's profile
            top_k: Number of results (default from config)
        
        Returns:
            List of top matching Program objects
        """
        results = self.search_with_profile(profile, top_k)
        return [program for program, _, _ in results]
    
    def get_program_score(
        self, 
        program: Program, 
        profile: StudentProfile
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Get detailed score for a single program.
        Useful for explaining why a specific program was/wasn't recommended.
        """
        user_fields, is_stem, corrected_interests = self._detect_user_fields(profile.interests)
        query = f"{corrected_interests} {profile.extracurriculars}".strip()
        
        # Get embedding score for this specific program
        query_emb = self._get_query_embedding(query)
        embedding_score = 0.0
        
        if query_emb is not None and program.embedding:
            prog_emb = np.array(program.embedding, dtype=np.float32)
            prog_norm = np.linalg.norm(prog_emb)
            if prog_norm > 0:
                prog_emb = prog_emb / prog_norm
                embedding_score = max(0, float(np.dot(query_emb, prog_emb)))
        
        final_score, breakdown = self._calculate_final_score(
            program=program,
            profile=profile,
            embedding_score=embedding_score,
            user_fields=user_fields,
            is_stem=is_stem,
            corrected_interests=corrected_interests
        )
        
        return final_score, breakdown.to_dict()
    
    def clear_cache(self) -> None:
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    @property
    def program_count(self) -> int:
        """Number of loaded programs"""
        return len(self.programs)
    
    @property
    def cache_size(self) -> int:
        """Number of cached embeddings"""
        return len(self._embedding_cache)