import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from job_details_models import JobDetails
from stepstone_server import handle_call_tool, session_manager


def test_get_job_details_prefers_index_and_falls_back_to_query():
    # Ensure we start with a clean slate for sessions
    session_manager.sessions.clear()

    jobs = [
        {
            "title": "Fraud Analyst",
            "company": "Example Corp",
            "description": "Investigate fraud.",
            "link": "https://example.com/jobs/1",
        },
        {
            "title": "Compliance Specialist",
            "company": "Example Corp",
            "description": "Ensure compliance.",
            "link": "https://example.com/jobs/2",
        },
    ]

    session_id = session_manager.create_session(results=jobs, search_terms=["fraud"], zip_code="10115", radius=10)

    fake_details = JobDetails(
        title="Compliance Specialist",
        company="Example Corp",
        location="Berlin",
        salary=None,
        employment_type=None,
        experience_level=None,
        posted_date=None,
        description="Ensure compliance.",
        requirements=[],
        responsibilities=[],
        benefits=[],
        company_details={},
        application_instructions="",
        contact_info={},
        job_url="https://example.com/jobs/2",
    )

    with patch("stepstone_server.JobDetailParser.parse_job_details", return_value=fake_details) as mock_parser:
        response = asyncio.run(
            handle_call_tool(
                "get_job_details",
                {"job_query": "Compliance", "session_id": session_id, "job_index": 2},
            )
        )

        assert response
        assert response[0].type == "text"
        mock_parser.assert_called_once_with("https://example.com/jobs/2")

        mock_parser.reset_mock()

        response = asyncio.run(
            handle_call_tool(
                "get_job_details",
                {"job_query": "Compliance Specialist", "session_id": session_id},
            )
        )

        assert response
        assert response[0].type == "text"
        mock_parser.assert_called_once_with("https://example.com/jobs/2")
