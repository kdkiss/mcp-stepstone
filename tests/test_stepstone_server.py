import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from stepstone_server import handle_call_tool, scraper


def test_search_jobs_handles_empty_results(monkeypatch):
    def mock_search_jobs(search_terms, zip_code, radius):
        return {term: [] for term in search_terms}

    monkeypatch.setattr(scraper, "search_jobs", mock_search_jobs)

    response = asyncio.run(
        handle_call_tool(
            "search_jobs",
            {"search_terms": ["qa"], "zip_code": "40210", "radius": 5},
        )
    )

    assert response, "Expected a response payload"
    assert response[0].type == "text"

    text = response[0].text
    assert "Total Jobs Found: 0" in text
    assert "No jobs were found for the provided search terms." in text
    assert "job_query='" not in text

