import asyncio
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from job_details_models import CompanyDetails, JobDetails  # noqa: E402
from stepstone_server import handle_call_tool, session_manager, JobDetailParser  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_sessions():
    session_manager.sessions.clear()


@pytest.fixture
def parser_spy(monkeypatch):
    details = JobDetails(
        title="Detailed Title",
        company="Example Co",
        location="Remote",
        salary=None,
        employment_type=None,
        experience_level=None,
        posted_date=None,
        description="Comprehensive role description",
        requirements=["Requirement"],
        responsibilities=["Responsibility"],
        benefits=["Benefit"],
        company_details=CompanyDetails(
            description="We craft great products",
            website="https://example.com/company",
        ),
        application_instructions="Apply via portal",
        contact_info={"email": "jobs@example.com"},
        job_url="http://example.com/details",
    )
    called_urls: list[str] = []

    def fake_parse(self, url):
        called_urls.append(url)
        return details

    monkeypatch.setattr(JobDetailParser, "parse_job_details", fake_parse)
    return called_urls, details


def test_get_job_details_by_index_uses_latest_session(parser_spy):
    called_urls, _ = parser_spy
    job = {
        "title": "Backend Engineer",
        "company": "ACME",
        "description": "Work on APIs",
        "link": "http://example.com/job",
    }
    session_manager.create_session(results=[job], search_terms=["backend"], zip_code="10115", radius=10)

    result = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "job_index": 1,
            },
        )
    )

    assert result
    assert "Detailed Title" in result[0].text
    assert "🛠 Responsibilities:" in result[0].text
    assert "Responsibility" in result[0].text
    assert "🏢 Company Profile:" in result[0].text
    assert "Description: We craft great products" in result[0].text
    assert "Website: https://example.com/company" in result[0].text
    assert "🧾 Application Instructions:" in result[0].text
    assert "Apply via portal" in result[0].text
    assert called_urls == ["http://example.com/job"]


def test_get_job_details_requires_identifier(parser_spy):
    response = asyncio.run(handle_call_tool("get_job_details", {}))
    assert response[0].text.startswith("Error: provide either a query string or a job_index")


def test_get_job_details_validates_job_index(parser_spy):
    response = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "job_index": 0,
            },
        )
    )
    assert response[0].text == "Error: job_index must be an integer greater than or equal to 1"


def test_get_job_details_handles_missing_session(parser_spy):
    response = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "query": "Engineer",
                "session_id": "missing-session",
            },
        )
    )

    assert "Session not found or expired" in response[0].text


def test_get_job_details_reports_missing_index(parser_spy):
    response = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "session_id": session_manager.create_session(
                    results=[{
                        "title": "Data Scientist",
                        "company": "DataCorp",
                        "description": "Analyze data",
                        "link": "http://example.com/datasci",
                    }],
                    search_terms=["data"],
                    zip_code="10115",
                    radius=10,
                ),
                "job_index": 2,
            },
        )
    )

    assert "No job found at the requested index" in response[0].text


def test_get_job_details_uses_query_when_provided(parser_spy):
    session_manager.create_session(
        results=[{
            "title": "Cloud Architect",
            "company": "Nimbus",
            "description": "Design infrastructure",
            "link": "http://example.com/cloud",
        }],
        search_terms=["cloud"],
        zip_code="10115",
        radius=10,
    )

    response = asyncio.run(
        handle_call_tool(
            "get_job_details",
            {
                "query": "Cloud Architect",
            },
        )
    )

    assert response
    assert "Detailed Title" in response[0].text
    assert "🛠 Responsibilities:" in response[0].text
