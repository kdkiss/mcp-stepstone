#!/usr/bin/env python3
"""
Data models for detailed job information in the Stepstone MCP server
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class JobDetails:
    """Comprehensive job details structure"""
    title: str
    company: str
    location: str
    salary: Optional[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    posted_date: Optional[str]
    description: str
    requirements: List[str]
    responsibilities: List[str]
    benefits: List[str]
    company_details: Dict[str, str]
    application_instructions: str
    contact_info: Dict[str, str]
    job_url: str
    raw_html: Optional[str] = None  # For debugging

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary": self.salary,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "posted_date": self.posted_date,
            "description": self.description,
            "requirements": self.requirements,
            "responsibilities": self.responsibilities,
            "benefits": self.benefits,
            "company_details": self.company_details,
            "application_instructions": self.application_instructions,
            "contact_info": self.contact_info,
            "job_url": self.job_url
        }

@dataclass
class SearchSession:
    """Session management for search results"""
    session_id: str
    search_terms: List[str]
    zip_code: str
    radius: int
    results: List[Dict[str, str]]
    timestamp: datetime
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session has expired"""
        return (datetime.now() - self.timestamp).total_seconds() > timeout_seconds

class JobDetailsError(Exception):
    """Base exception for job details retrieval"""
    pass

class JobNotFoundError(JobDetailsError):
    """Raised when job cannot be identified"""
    pass

class PageParseError(JobDetailsError):
    """Raised when job page cannot be parsed"""
    pass

class NetworkError(JobDetailsError):
    """Raised when network request fails"""
    pass