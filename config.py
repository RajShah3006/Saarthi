# config.py - Configuration with validation
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger("saarthi.config")


@dataclass
class Config:
    """Application configuration"""
    
    # API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Paths
    DATA_DIR: Path = None
    PROGRAMS_FILE: Path = None
    
    # Limits
    MAX_INTERESTS_LENGTH: int = 500
    MAX_LOCATION_LENGTH: int = 100
    MAX_FOLLOWUP_LENGTH: int = 1000
    TOP_K_PROGRAMS: int = 10  # Top 10 programs
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # UI
    THEME_PRIMARY: str = "#3b82f6"
    THEME_SECONDARY: str = "#8b5cf6"
    THEME_ACCENT: str = "#f59e0b"
    
    # Grade options
    GRADE_OPTIONS: List[str] = None
    
    def __init__(self):
        self.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
        self._setup_paths()
        self.GRADE_OPTIONS = [
            "Grade 9", "Grade 10", "Grade 11", 
            "Grade 12", "Gap Year", "University Transfer"
        ]
        self._log_config()
    
    def _setup_paths(self):
        """Find programs.json in various locations"""
        possible_files = [
            Path("programs.json"),
            Path("./programs.json"),
            Path("data/programs.json"),
            Path("./data/programs.json"),
            Path("/data/programs.json"),
            Path("university_data_cached.json"),
            Path("./university_data_cached.json"),
        ]
        
        for path in possible_files:
            if path.exists():
                self.PROGRAMS_FILE = path.resolve()
                self.DATA_DIR = self.PROGRAMS_FILE.parent
                logger.info(f"✅ Found programs file: {self.PROGRAMS_FILE}")
                return
        
        # Default
        self.DATA_DIR = Path("data")
        self.DATA_DIR.mkdir(exist_ok=True)
        self.PROGRAMS_FILE = self.DATA_DIR / "programs.json"
        logger.warning(f"⚠️ Programs file not found, will use: {self.PROGRAMS_FILE}")
    
    def _log_config(self):
        logger.info(f"Config: API={'✓' if self.GEMINI_API_KEY else '✗'}, "
                   f"Programs={self.PROGRAMS_FILE}, Exists={self.PROGRAMS_FILE.exists()}")