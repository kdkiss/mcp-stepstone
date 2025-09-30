import sys
from datetime import timedelta
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


def test_get_active_session_overview_formats_metadata_and_sorts():
    manager = SessionManager()

    old_session_id = manager.create_session(
        results=[{"title": "Data Scientist", "company": "ACME"}],
        search_terms=["data scientist"],
        zip_code="10115",
        radius=10,
    )

    new_session_id = manager.create_session(
        results=[{"title": "Backend Engineer", "company": "Beta"}],
        search_terms=None,
        zip_code="20095",
        radius=15,
    )

    # Make the first session older so that ordering can be asserted reliably
    manager.sessions[old_session_id].timestamp -= timedelta(seconds=120)
    manager.sessions[new_session_id].timestamp -= timedelta(seconds=30)

    overview = manager.get_active_session_overview()

    assert [entry["session_id"] for entry in overview] == [new_session_id, old_session_id]

    newest = overview[0]
    assert newest == {
        "session_id": new_session_id,
        "search_terms": "None",
        "location": "20095 (±15km)",
        "result_count": 1,
        "age_seconds": newest["age_seconds"],
    }
    assert newest["age_seconds"] >= 30
    assert newest["age_seconds"] < 180

    oldest = overview[1]
    assert oldest["search_terms"] == "data scientist"
    assert oldest["location"] == "10115 (±10km)"
    assert oldest["result_count"] == 1
