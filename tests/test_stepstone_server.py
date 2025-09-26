import pytest

import stepstone_server


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio("asyncio")
async def test_search_jobs_no_results(monkeypatch, caplog):
    search_terms = ["term1", "term2"]

    def fake_search_jobs(terms, zip_code, radius):
        assert terms == search_terms
        return {term: [] for term in terms}

    def fake_create_session(results, *args, **kwargs):
        assert results == []
        return "test-session"

    monkeypatch.setattr(stepstone_server.scraper, "search_jobs", fake_search_jobs)
    monkeypatch.setattr(stepstone_server.session_manager, "create_session", fake_create_session)

    with caplog.at_level("INFO"):
        response = await stepstone_server.handle_call_tool(
            "search_jobs",
            {"search_terms": search_terms, "zip_code": "40210", "radius": 5},
        )

    assert response
    message = response[0].text

    assert "Total Jobs Found: 0" in message
    assert "No jobs found for this search term." in message
    assert "refining your search terms" in message

    assert any("returned no results" in record.getMessage() for record in caplog.records)

