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
# services/program_search.py
import json
import os
from typing import List

import numpy as np

from config import Config
from models import Program, StudentProfile
from services.llm_client import EmbeddingClient


class ProgramSearchService:
    def __init__(self, config: Config):
        self.config = config
        self.embedding_client = EmbeddingClient(config=config)

        self.programs: List[Program] = []
        self.program_embeddings = None

        self._load_programs()

    def _load_programs(self):
        programs_path = self.config.PROGRAMS_PATH
        if not os.path.exists(programs_path):
            raise FileNotFoundError(f"Programs file not found: {programs_path}")

        with open(programs_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.programs = [Program.from_dict(p) for p in raw if isinstance(p, dict)]
        self.program_embeddings = np.array([p.get("embedding", []) for p in raw], dtype=np.float32)

    def search_with_profile(self, profile: StudentProfile, top_k: int = 10) -> List[Program]:
        """
        Search programs using embeddings + simple filters.
        Minimal change: include preferences text in query so results feel more personalized.
        """
        pref_parts = []
        if getattr(profile, "preferences", None):
            pref_parts.extend([p for p in profile.preferences if p])
        if getattr(profile, "preferences_other", ""):
            pref_parts.append(profile.preferences_other)
        prefs_text = " ".join(pref_parts).strip()

        query = f"{profile.interests} {profile.extracurriculars} {prefs_text}".strip()
        if not query:
            query = profile.interests.strip() or "Ontario university programs"

        query_emb = self.embedding_client.embed_text(query)
        if query_emb is None:
            return self.programs[:top_k]

        query_emb = np.array(query_emb, dtype=np.float32)
        denom = (np.linalg.norm(self.program_embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8)
        sims = (self.program_embeddings @ query_emb) / denom

        # rank
        idxs = np.argsort(-sims)[:top_k]
        results: List[Program] = []
        for i in idxs:
            p = self.programs[int(i)]
            # clone shallow
            p2 = Program(
                name=p.name,
                url=p.url,
                prerequisites=p.prerequisites,
                admission_average=p.admission_average,
                match_percent=float(sims[int(i)]),
                match_reasons=[],
            )
            results.append(p2)

        return results
