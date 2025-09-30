#!/usr/bin/env python3
"""Session management for storing and retrieving search results."""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from job_details_models import SearchSession


logger = logging.getLogger(__name__)

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
            search_terms=search_terms if search_terms is not None else [],
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
            if not isinstance(job, dict):
                logger.warning("Skipping non-dictionary job entry: %r", job)
                continue

            title = job.get("title")
            if not isinstance(title, str):
                logger.warning("Job missing valid title; skipping entry: %r", job)
                continue

            if query_lower in title.lower():
                return job

        # Try company match
        for job in session.results:
            if not isinstance(job, dict):
                logger.warning("Skipping non-dictionary job entry: %r", job)
                continue

            company = job.get("company")
            if not isinstance(company, str):
                logger.warning("Job missing valid company; skipping entry: %r", job)
                continue

            if query_lower in company.lower():
                return job

        # Try partial title match
        query_words = query_lower.split()
        for job in session.results:
            if not isinstance(job, dict):
                logger.warning("Skipping non-dictionary job entry: %r", job)
                continue

            title = job.get("title")
            if not isinstance(title, str):
                logger.warning("Job missing valid title; skipping entry: %r", job)
                continue

            title_words = title.lower().split()
            if any(word in title_words for word in query_words):
                return job
        
        return None

    def get_job_by_index(self, session_id: str, job_index: int) -> Optional[Dict[str, str]]:
        """Retrieve a job by its 1-based index within a session."""
        session = self.get_session(session_id)
        if not session:
            return None

        # Convert to zero-based index for list access
        zero_based_index = job_index - 1
        if zero_based_index < 0 or zero_based_index >= len(session.results):
            return None

        return session.results[zero_based_index]
    
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
        search_terms_text = ', '.join(session.search_terms) if session.search_terms else "None"
        summary += f"Search Terms: {search_terms_text}\n"
        summary += f"Location: {session.zip_code} (±{session.radius}km)\n"
        summary += f"Results: {len(session.results)} jobs found\n"
        summary += f"Search Time: {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        self._cleanup_expired_sessions()
        return list(self.sessions.keys())

    def get_active_session_overview(self) -> List[Dict[str, object]]:
        """Return lightweight metadata for each active session.

        The overview is sorted by most recent session first so clients can
        easily present the freshest results to the user. Each overview entry
        contains human friendly values that are ready for display without
        requiring additional processing downstream.
        """

        self._cleanup_expired_sessions()

        if not self.sessions:
            return []

        current_time = datetime.now()
        overview: List[Dict[str, object]] = []

        # Sort sessions by recency so that the freshest search appears first
        for session in sorted(
            self.sessions.values(), key=lambda s: s.timestamp, reverse=True
        ):
            search_terms_text = (
                ", ".join(session.search_terms) if session.search_terms else "None"
            )

            overview.append(
                {
                    "session_id": session.session_id,
                    "search_terms": search_terms_text,
                    "location": f"{session.zip_code} (±{session.radius}km)",
                    "result_count": len(session.results),
                    "age_seconds": max(
                        0,
                        int((current_time - session.timestamp).total_seconds()),
                    ),
                }
            )

        return overview

# Global session manager instance
session_manager = SessionManager()
