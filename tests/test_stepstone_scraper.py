import sys
from pathlib import Path
from urllib.parse import unquote

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from job_detail_parser import JobDetailParser
from job_details_models import JobDetails
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


def test_search_jobs_normalizes_terms(monkeypatch, scraper):
    observed_terms = []

    def fake_fetch(self, url):
        observed_terms.append(unquote(url.split("/jobs/")[1].split("/in-")[0]))
        return []

    monkeypatch.setattr(StepstoneJobScraper, "fetch_job_listings", fake_fetch)

    results = scraper.search_jobs([" Fraud ", "fraud", "DATA", "data", ""], zip_code="12345", radius=15)

    assert observed_terms == ["Fraud", "DATA"]
    assert results == {"Fraud": [], "DATA": []}


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
