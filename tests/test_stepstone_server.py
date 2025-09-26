import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from stepstone_server import handle_call_tool, session_manager


@pytest.fixture(autouse=True)
def clear_sessions():
    session_manager.sessions.clear()
    yield
    session_manager.sessions.clear()


def _create_session_with_jobs():
    job_results = [
        {
            "title": "Fraud Analyst",
            "company": "Acme Corp",
            "description": "Investigate suspicious activity",
            "link": "https://example.com/fraud-analyst",
        },
        {
            "title": "Compliance Specialist",
            "company": "Beta Ltd",
            "description": "Ensure regulatory adherence",
            "link": "https://example.com/compliance-specialist",
        },
    ]

    return session_manager.create_session(results=job_results)


def _fake_job_details(title: str) -> SimpleNamespace:
    return SimpleNamespace(
        title=title,
        company="Acme Corp",
        location="Düsseldorf",
        salary=None,
        employment_type=None,
        experience_level=None,
        posted_date=None,
        description="Detailed description",
        requirements=[],
        responsibilities=[],
        benefits=[],
        company_details={},
        application_instructions="",
        contact_info={},
        job_url="https://example.com/job",
        raw_html=None,
    )


def test_get_job_details_by_index_without_query():
    session_id = _create_session_with_jobs()
    details = _fake_job_details("Fraud Analyst")

    with patch("stepstone_server.JobDetailParser.parse_job_details", return_value=details):
        response = asyncio.run(
            handle_call_tool(
                "get_job_details",
                {
                    "session_id": session_id,
                    "job_index": 1,
                },
            )
        )

    assert response
    assert "📋 Job Details: Fraud Analyst" in response[0].text


def test_get_job_details_by_index_out_of_range():
    session_id = _create_session_with_jobs()

    response = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "session_id": session_id,
                "job_index": 3,
            },
        )
    )

    assert response
    assert "Error: job_index 3 is out of range" in response[0].text


def test_get_job_details_index_takes_precedence_over_query():
    session_id = _create_session_with_jobs()
    details = _fake_job_details("Compliance Specialist")

    with patch("stepstone_server.JobDetailParser.parse_job_details", return_value=details):
        response = asyncio.run(
            handle_call_tool(
                "get_job_details",
                {
                    "session_id": session_id,
                    "job_index": 2,
                    "job_query": "Non-matching query",
                },
            )
        )

    assert response
    body = response[0].text
    assert "📋 Job Details: Compliance Specialist" in body
    assert "Non-matching query" not in body

