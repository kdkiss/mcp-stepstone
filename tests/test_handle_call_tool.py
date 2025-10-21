import asyncio
import sys
from pathlib import Path
from typing import Dict, List

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import stepstone_server
from job_details_models import JobDetails, CompanyDetails
from session_manager import session_manager
from stepstone_server import JobDetailParser, handle_call_tool, scraper


@pytest.fixture(autouse=True)
def clear_sessions():
    session_manager.sessions.clear()
    yield
    session_manager.sessions.clear()


def test_handle_call_tool_search_jobs_success(monkeypatch):
    sample_jobs: Dict[str, List[Dict[str, str]]] = {
        "fraud": [
            {
                "title": "Fraud Analyst",
                "company": "Secure Corp",
                "description": "Investigate fraud cases",
                "link": "https://example.com/job/1",
            }
        ]
    }

    monkeypatch.setattr(scraper, "search_jobs", lambda *args, **kwargs: sample_jobs)

    response = asyncio.run(handle_call_tool(
        "search_jobs",
        {"search_terms": ["fraud"], "zip_code": "40210", "radius": 10},
    ))

    assert len(response) == 1
    text = response[0].text
    assert "Total Jobs Found: 1" in text
    assert "Fraud Analyst" in text
    assert "Session ID:" in text


def test_handle_call_tool_search_jobs_empty_results(monkeypatch):
    monkeypatch.setattr(scraper, "search_jobs", lambda *args, **kwargs: {"fraud": []})

    response = asyncio.run(handle_call_tool("search_jobs", {"search_terms": ["fraud"]}))

    text = response[0].text
    assert "Total Jobs Found: 0" in text
    assert "No jobs found for this search term." in text
    assert "Try refining your search terms or expanding the radius." in text


def test_handle_call_tool_search_jobs_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(scraper, "search_jobs", fail)

    response = asyncio.run(handle_call_tool("search_jobs", {"search_terms": ["fraud"]}))

    assert "Error performing job search: network down" in response[0].text


def test_handle_call_tool_search_jobs_timeout(monkeypatch):
    monkeypatch.setattr(scraper, "search_jobs", lambda *args, **kwargs: {"fraud": []})
    monkeypatch.setenv("REQUEST_TIMEOUT", "1")

    async def slow_to_thread(func, *args, **kwargs):
        await asyncio.sleep(1.2)
        return func(*args, **kwargs)

    monkeypatch.setattr(stepstone_server.asyncio, "to_thread", slow_to_thread)

    response = asyncio.run(handle_call_tool("search_jobs", {"search_terms": ["fraud"]}))

    assert "took too long to respond" in response[0].text


def test_handle_call_tool_get_job_details_success(monkeypatch):
    job = {
        "title": "Fraud Analyst",
        "company": "Secure Corp",
        "description": "Investigate fraud cases",
        "link": "https://example.com/job/1",
    }
    session_id = session_manager.create_session([job], ["fraud"], "40210", 5)

    fake_details = JobDetails(
        title="Fraud Analyst",
        company="Secure Corp",
        location="Berlin",
        salary=None,
        employment_type="Vollzeit",
        experience_level="Senior",
        posted_date=None,
        description="Detailed description",
        requirements=["Skill"],
        responsibilities=["Task"],
        benefits=["Benefit"],
        company_details=CompanyDetails(
            description="Leading security firm",
            website="https://secure.example.com",
        ),
        application_instructions="Apply online",
        contact_info={},
        job_url="https://example.com/job/1",
    )

    monkeypatch.setattr(JobDetailParser, "parse_job_details", lambda self, url: fake_details)

    response = asyncio.run(handle_call_tool(
        "get_job_details",
        {"query": "Fraud Analyst", "session_id": session_id},
    ))

    text = response[0].text
    assert "📋 Job Details: Fraud Analyst" in text
    assert "🧠 Experience Level: Senior" in text
    assert "🛠 Responsibilities:" in text
    assert "Task" in text
    assert "🧾 Application Instructions:" in text
    assert "Apply online" in text
    assert "Apply: https://example.com/job/1" in text
    assert "Company Profile" in text


def test_handle_call_tool_get_job_details_no_match(monkeypatch):
    session_manager.create_session(
        [
            {
                "title": "Fraud Analyst",
                "company": "Secure Corp",
                "description": "Investigate fraud cases",
                "link": "https://example.com/job/1",
            }
        ],
        ["fraud"],
        "40210",
        5,
    )

    response = asyncio.run(handle_call_tool(
        "get_job_details",
        {"query": "Data Scientist", "session_id": list(session_manager.sessions.keys())[0]},
    ))

    assert response[0].text == "No job found matching: Data Scientist"


def test_handle_call_tool_get_job_details_error(monkeypatch):
    job = {
        "title": "Fraud Analyst",
        "company": "Secure Corp",
        "description": "Investigate fraud cases",
        "link": "https://example.com/job/1",
    }
    session_id = session_manager.create_session([job], ["fraud"], "40210", 5)

    def fail(self, url):
        raise RuntimeError("parse failure")

    monkeypatch.setattr(JobDetailParser, "parse_job_details", fail)

    response = asyncio.run(handle_call_tool(
        "get_job_details",
        {"query": "Fraud Analyst", "session_id": session_id},
    ))

    assert "Error retrieving job details: parse failure" in response[0].text


def test_handle_call_tool_get_job_details_timeout(monkeypatch):
    job = {
        "title": "Fraud Analyst",
        "company": "Secure Corp",
        "description": "Investigate fraud cases",
        "link": "https://example.com/job/1",
    }
    session_id = session_manager.create_session([job], ["fraud"], "40210", 5)

    def parse_should_not_run(self, url):  # pragma: no cover - defensive guard
        raise AssertionError("parse_job_details should not execute during timeout test")

    monkeypatch.setattr(JobDetailParser, "parse_job_details", parse_should_not_run)
    monkeypatch.setenv("REQUEST_TIMEOUT", "1")

    async def slow_to_thread(func, *args, **kwargs):
        await asyncio.sleep(1.2)
        return func(*args, **kwargs)

    monkeypatch.setattr(stepstone_server.asyncio, "to_thread", slow_to_thread)

    response = asyncio.run(handle_call_tool(
        "get_job_details",
        {"query": "Fraud Analyst", "session_id": session_id},
    ))

    assert "Fetching detailed information took too long" in response[0].text
