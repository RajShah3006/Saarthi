# services/session.py - Session-only auth (no passwords, no persistence)
import logging
from typing import Dict, Optional
from datetime import datetime

from config import Config
from models import Session

logger = logging.getLogger("saarthi.session")


class SessionManager:
    """In-memory session management (no persistence, no passwords)"""
    
    def __init__(self, config: Config):
        self.config = config
        self.sessions: Dict[str, Session] = {}
    
    def create_session(self, name: str) -> Session:
        """Create a new session"""
        session = Session(name=name or "Student")
        self.sessions[session.id] = session
        
        logger.info(f"Created session {session.id[:8]}... for {name}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, returns None if expired or not found"""
        if not session_id:
            return None
        
        session = self.sessions.get(session_id)
        
        if not session:
            logger.debug(f"Session {session_id[:8]}... not found")
            return None
        
        if not session.is_valid(self.config.SESSION_TIMEOUT_MINUTES):
            logger.info(f"Session {session_id[:8]}... expired")
            del self.sessions[session_id]
            return None
        
        return session
    
    def cleanup_expired(self):
        """Remove expired sessions (call periodically if needed)"""
        expired = [
            sid for sid, session in self.sessions.items()
            if not session.is_valid(self.config.SESSION_TIMEOUT_MINUTES)
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")