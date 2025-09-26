import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from session_manager import SessionManager


def test_get_session_summary_without_search_terms():
    manager = SessionManager()
    job_results = [
        {
            "title": "Software Engineer",
            "company": "Example Corp",
            "location": "Remote",
        }
    ]

    session_id = manager.create_session(results=job_results)

    # The session should normalize missing search terms to an empty list
    session = manager.get_session(session_id)
    assert session is not None
    assert session.search_terms == []

    summary = manager.get_session_summary(session_id)
    assert summary is not None
    assert "Search Terms: None" in summary


def test_find_job_in_session_skips_malformed_entries():
    manager = SessionManager()
    job_results = [
        {"title": None, "company": "Alpha Corp"},
        {"company": "Beta Corp"},
        "not a dict",
        {"title": "Senior Data Scientist", "company": "Gamma"},
    ]

    session_id = manager.create_session(results=job_results)

    match = manager.find_job_in_session(session_id, "data scientist")
    assert match is not None
    assert match["title"] == "Senior Data Scientist"


def test_find_job_in_session_returns_none_when_all_entries_invalid():
    manager = SessionManager()
    job_results = [
        {"title": None, "company": None},
        {"title": 123, "company": "Numeric Title"},
        {},
        "not a dict",
    ]

    session_id = manager.create_session(results=job_results)

    match = manager.find_job_in_session(session_id, "engineer")
    assert match is None
