#!/usr/bin/env python3
"""
Session management for storing and retrieving search results
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from job_details_models import SearchSession

class SessionManager:
    """Manages search sessions for follow-up questions"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, SearchSession] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, results: List[Dict[str, str]], search_terms: List[str] = None, zip_code: str = "40210", radius: int = 5) -> str:
        """
        Create a new search session
        
        Args:
            search_terms: List of search terms used
            zip_code: ZIP code used for search
            radius: Search radius in km
            results: List of job results
            
        Returns:
            Session ID for the new session
        """
        session_id = str(uuid.uuid4())
        
        session = SearchSession(
            session_id=session_id,
            search_terms=search_terms,
            zip_code=zip_code,
            radius=radius,
            results=results,
            timestamp=datetime.now()
        )
        
        self.sessions[session_id] = session
        self._cleanup_expired_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SearchSession]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SearchSession object or None if not found/expired
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        if session.is_expired(self.session_timeout):
            del self.sessions[session_id]
            return None
        
        return session
    
    def find_job_in_session(self, session_id: str, job_query: str) -> Optional[Dict[str, str]]:
        """
        Find a specific job in a session based on user query
        
        Args:
            session_id: The session ID
            job_query: User's job query (e.g., "AML Specialist")
            
        Returns:
            Job dictionary or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Normalize query for matching
        query_lower = job_query.lower().strip()
        
        # Try exact title match first
        for job in session.results:
            if query_lower in job['title'].lower():
                return job
        
        # Try company match
        for job in session.results:
            if query_lower in job['company'].lower():
                return job
        
        # Try partial title match
        query_words = query_lower.split()
        for job in session.results:
            title_words = job['title'].lower().split()
            if any(word in title_words for word in query_words):
                return job
        
        return None
    
    def get_recent_session(self) -> Optional[SearchSession]:
        """
        Get the most recent active session
        
        Returns:
            Most recent SearchSession or None if no active sessions
        """
        self._cleanup_expired_sessions()
        
        if not self.sessions:
            return None
        
        # Return the most recent session
        return max(self.sessions.values(), key=lambda s: s.timestamp)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        Get a human-readable summary of a session
        
        Args:
            session_id: The session ID
            
        Returns:
            Summary string or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        summary = f"Search Session: {session_id[:8]}...\n"
        summary += f"Search Terms: {', '.join(session.search_terms)}\n"
        summary += f"Location: {session.zip_code} (±{session.radius}km)\n"
        summary += f"Results: {len(session.results)} jobs found\n"
        summary += f"Search Time: {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        self._cleanup_expired_sessions()
        return list(self.sessions.keys())

# Global session manager instance
session_manager = SessionManager()