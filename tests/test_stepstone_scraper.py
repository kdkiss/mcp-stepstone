import sys
from pathlib import Path
from urllib.parse import unquote

import pytest
import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from job_detail_parser import JobDetailParser
from job_details_models import JobDetails, NetworkError
from stepstone_server import StepstoneJobScraper


@pytest.fixture
def scraper():
    return StepstoneJobScraper()


def test_search_jobs_returns_results_for_each_term(monkeypatch, scraper):
    sample_results = {
        "fraud": [
            {
                "title": "Fraud Analyst",
                "company": "Secure Corp",
                "description": "Investigate fraud cases",
                "link": "https://www.stepstone.de/stellenangebote--fraud-analyst-inline.html",
            }
        ],
        "data": [
            {
                "title": "Data Scientist",
                "company": "DataWorks",
                "description": "Build data models",
                "link": "https://www.stepstone.de/stellenangebote--data-scientist-inline.html",
            }
        ],
    }

    def fake_fetch(self, url):
        term = unquote(url.split("/jobs/")[1].split("/in-")[0])
        return sample_results[term]

    monkeypatch.setattr(StepstoneJobScraper, "fetch_job_listings", fake_fetch)

    results = scraper.search_jobs(["fraud", "data"], zip_code="12345", radius=15)

    assert results == {
        "fraud": sample_results["fraud"],
        "data": sample_results["data"],
    }


def test_search_jobs_with_no_terms_returns_empty(monkeypatch, scraper):
    call_count = 0

    def fake_fetch(self, url):
        nonlocal call_count
        call_count += 1
        return []

    monkeypatch.setattr(StepstoneJobScraper, "fetch_job_listings", fake_fetch)

    assert scraper.search_jobs([]) == {}
    assert call_count == 0


SAMPLE_HTML = """
<html>
    <body>
        <h1 data-testid="job-title">Senior Fraud Analyst</h1>
        <span data-testid="company-name">Secure Corp</span>
        <div data-testid="job-location">Berlin, Germany</div>
        <div data-testid="salary">60.000 € pro Jahr</div>
        <div data-testid="employment-type">Vollzeit</div>
        <div data-testid="experience-level">Senior</div>
        <div>Veröffentlicht am 12.03.2024</div>
        <section class="job-description">Analyze fraud risks<br/>Lead team</section>
        <section data-testid="requirements">
            <ul>
                <li>5+ years experience</li>
                <li>SQL expertise</li>
            </ul>
        </section>
        <section data-testid="responsibilities">
            <ul>
                <li>Monitor alerts</li>
                <li>Coordinate investigations</li>
            </ul>
        </section>
        <section data-testid="benefits">
            <ul>
                <li>Remote work</li>
                <li>Annual bonus</li>
            </ul>
        </section>
        <div data-testid="company-description">We fight fraud.</div>
        <div data-testid="application-instructions">Submit via portal.</div>
        <div>Kontakt: Anna Schmidt</div>
        <div>Email: jobs@example.com</div>
        <div>Phone: +49 123 456789</div>
        <a href="https://company.example.com">Company Site</a>
    </body>
</html>
"""


def test_parse_job_details_extracts_expected_fields(monkeypatch):
    parser = JobDetailParser()

    monkeypatch.setattr(JobDetailParser, "fetch_job_page", lambda self, url: SAMPLE_HTML)

    details = parser.parse_job_details("https://www.stepstone.de/job/123")

    assert isinstance(details, JobDetails)
    assert details.title == "Senior Fraud Analyst"
    assert details.company == "Secure Corp"
    assert details.location == "Berlin, Germany"
    assert details.salary == "60.000 € pro Jahr"
    assert details.employment_type == "Vollzeit"
    assert details.experience_level == "Senior"
    assert details.posted_date == "12.03.2024"
    assert "Analyze fraud risks" in details.description
    assert details.requirements == ["5+ years experience", "SQL expertise"]
    assert details.responsibilities == ["Monitor alerts", "Coordinate investigations"]
    assert details.benefits == ["Remote work", "Annual bonus"]
    assert details.company_details["description"] == "We fight fraud."
    assert details.company_details["website"] == "https://company.example.com"
    assert details.application_instructions == "Submit via portal."
    assert details.contact_info["email"] == "jobs@example.com"
    assert details.contact_info["phone"] == "+49 123 456789"
    assert details.contact_info["contact_person"] == "Anna Schmidt"
    assert details.job_url == "https://www.stepstone.de/job/123"


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_fetch_job_listings_applies_throttling_and_backoff(monkeypatch):
    html = """
    <div id="app-unifiedResultlist">
        <article data-testid="job-item">
            <a href="/stellenangebote--example-role--123-inline.html">Example Role</a>
            <span class="company-name">Example Corp</span>
            <p class="description">Exciting work</p>
        </article>
    </div>
    """

    scraper = StepstoneJobScraper(
        min_delay=0.1,
        max_delay=0.1,
        max_retries=3,
        backoff_factor=2.0,
        user_agents=("UA-1", "UA-2"),
    )

    sleep_calls = []

    def fake_sleep(duration):
        sleep_calls.append(duration)

    monkeypatch.setattr("stepstone_server.time.sleep", fake_sleep)
    monkeypatch.setattr("stepstone_server.random.uniform", lambda a, b: 0.1)

    headers_seen = []
    call_count = {"value": 0}

    def fake_get(self, url, headers, timeout):
        call_count["value"] += 1
        headers_seen.append(headers["User-Agent"])
        if call_count["value"] < 3:
            raise requests.RequestException("temporary error")
        return DummyResponse(html)

    monkeypatch.setattr(requests.Session, "get", fake_get, raising=False)

    results = scraper.fetch_job_listings("https://example.com/jobs")

    assert len(results) == 1
    assert call_count["value"] == 3
    assert headers_seen == ["UA-1", "UA-2", "UA-1"]
    assert sleep_calls == [pytest.approx(0.1), pytest.approx(0.2), pytest.approx(0.1), pytest.approx(0.4), pytest.approx(0.1)]


def test_fetch_job_page_uses_backoff_and_rotating_agents(monkeypatch):
    parser = JobDetailParser(
        min_delay=0.1,
        max_delay=0.1,
        max_retries=2,
        backoff_factor=2.0,
        user_agents=("UA-1", "UA-2"),
    )

    sleep_calls = []

    def fake_sleep(duration):
        sleep_calls.append(duration)

    monkeypatch.setattr("job_detail_parser.time.sleep", fake_sleep)
    monkeypatch.setattr("job_detail_parser.random.uniform", lambda a, b: 0.1)

    headers_seen = []
    call_count = {"value": 0}

    def fake_get(self, url, headers, timeout):
        call_count["value"] += 1
        headers_seen.append(headers["User-Agent"])
        raise requests.RequestException("failure")

    monkeypatch.setattr(requests.Session, "get", fake_get, raising=False)

    with pytest.raises(NetworkError):
        parser.fetch_job_page("https://example.com/job")

    assert call_count["value"] == 2
    assert headers_seen == ["UA-1", "UA-2"]
    assert sleep_calls == [pytest.approx(0.1), pytest.approx(0.2), pytest.approx(0.1)]
