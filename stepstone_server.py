#!/usr/bin/env python3
"""
Stepstone Job Search MCP Server

A Model Context Protocol server for searching job listings on Stepstone.de
Compatible with Smithery and other MCP clients.
"""

import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool
import mcp.types as types

# Import new modules
from job_detail_parser import JobDetailParser
from session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stepstone-server")


class StepstoneJobScraper:
    """Job scraper for Stepstone.de"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_job_listings(self, url: str) -> List[Dict[str, str]]:
        """Fetch job listings from a Stepstone URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            container = soup.find("div", id="app-unifiedResultlist")

            if not container:
                logger.warning(f"No job container found for URL: {url}")
                return []

            jobs = []
            seen_links = set()

            for article in container.find_all(
                "article", attrs={"data-testid": "job-item"}
            ):
                # Find all links in the article
                all_links = article.find_all("a", href=True)

                job_link = None
                job_title = None

                # First, look for job posting links with the correct pattern
                for link_elem in all_links:
                    href = link_elem.get("href", "")

                    # Check for actual job posting URLs (contain stellenangebote and inline.html)
                    if re.search(r"/stellenangebote--.*--\d+-inline\.html", href):
                        job_link = link_elem
                        job_title = link_elem.get_text(strip=True)
                        break

                # If no job posting link found, look for relative links starting with /stellenangebote
                if not job_link:
                    for link_elem in all_links:
                        href = link_elem.get("href", "")
                        # Skip company profile links and external links
                        if "/cmp/" in href or href.startswith("http"):
                            continue
                        # Look for job posting links that start with /stellenangebote
                        if (
                            href.startswith("/stellenangebote")
                            and "inline.html" in href
                        ):
                            job_link = link_elem
                            job_title = link_elem.get_text(strip=True)
                            break

                if not job_link:
                    continue

                # Extract job title from h2/h3 if available, otherwise use link text
                if not job_title or len(job_title) < 5:
                    title_elem = (
                        article.find("h2")
                        or article.find("h3")
                        or article.find(
                            "span", attrs={"data-testid": re.compile("job-title")}
                        )
                    )
                    if title_elem:
                        job_title = title_elem.get_text(strip=True)

                title = (
                    job_title if job_title and len(job_title) > 0 else "Unknown Title"
                )

                link = job_link["href"]

                # Ensure absolute URL
                if not link.startswith("http"):
                    link = f"https://www.stepstone.de{link}"

                # Skip duplicates and company profile links
                if link in seen_links or "/cmp/" in link:
                    continue
                seen_links.add(link)

                # Extract company information
                company_elem = (
                    article.find("span", class_=re.compile("company|employer"))
                    or article.find(
                        "a", attrs={"data-testid": re.compile("company|employer")}
                    )
                    or article.find(
                        "span", attrs={"data-testid": re.compile("company|employer")}
                    )
                )
                company = (
                    company_elem.get_text(strip=True)
                    if company_elem
                    else "Unknown Company"
                )

                # Extract short description
                desc_elem = (
                    article.find("p", class_=re.compile("description|snippet|teaser"))
                    or article.find(
                        "div", class_=re.compile("description|snippet|teaser")
                    )
                    or article.find(
                        "span", class_=re.compile("description|snippet|teaser")
                    )
                )
                description = (
                    desc_elem.get_text(strip=True)[:200] + "..."
                    if desc_elem and desc_elem.get_text(strip=True)
                    else "No description available"
                )

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "description": description,
                        "link": link,
                    }
                )

            logger.info(f"Found {len(jobs)} jobs for URL: {url}")
            return jobs

        except requests.RequestException as e:
            logger.error(f"Request failed for URL {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping URL {url}: {e}")
            return []

    def build_search_url(
        self, term: str, zip_code: str = "40210", radius: int = 5
    ) -> str:
        """Build Stepstone search URL"""
        encoded_term = quote(term)
        return f"https://www.stepstone.de/jobs/{encoded_term}/in-{zip_code}?radius={radius}&searchOrigin=Homepage_top-search&q=%22{encoded_term}%22"

    def _search_single_term(
        self, term: str, zip_code: str, radius: int
    ) -> tuple[str, List[Dict[str, str]]]:
        """Helper for concurrently searching a single term."""
        logger.info(f"Searching for jobs with term: {term}")
        url = self.build_search_url(term, zip_code, radius)
        jobs = self.fetch_job_listings(url)
        return term, jobs

    def search_jobs(
        self, search_terms: List[str], zip_code: str = "40210", radius: int = 5
    ) -> Dict[str, List[Dict[str, str]]]:
        """Search for jobs using multiple terms"""
        results: Dict[str, List[Dict[str, str]]] = {}

        if not search_terms:
            return results

        max_workers = min(8, len(search_terms))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._search_single_term, term, zip_code, radius)
                for term in search_terms
            ]

            for future in as_completed(futures):
                term, jobs = future.result()
                results[term] = jobs

        ordered_results = {term: results.get(term, []) for term in search_terms}
        return ordered_results


# Initialize the server
server = Server("stepstone-job-search")
scraper = StepstoneJobScraper()


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="stepstone://search-help",
            name="Stepstone Job Search Help",
            description="Information about how to use the Stepstone job search functionality",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    if uri == "stepstone://search-help":
        return """Stepstone Job Search MCP Server

This server allows you to search for jobs on Stepstone.de.

Available tools:
- search_jobs: Search for jobs using multiple search terms
- get_job_details: Retrieve a single job from your most recent or specified search session

Parameters:
- search_terms: List of job search terms (e.g., ["fraud", "betrug", "data analyst"])
- zip_code: German postal code for location-based search (default: "40210")
- radius: Search radius in kilometers (default: 5)
- job_index: 1-based index into the stored results of a previous search session. Takes precedence over job_query when provided.
- job_query: Text used to fuzzy-match a job when job_index is not supplied.

Validation messages:
- "Error: job_index must be a positive integer" appears when non-positive numbers are supplied.
- "Error: job_index X is out of range" appears when the selected index is not present in the stored results.
- "Error: Provide either job_index or job_query" appears when neither selector is supplied.

Example usage:
Use the search_jobs tool with terms like "fraud specialist", "betrug", "compliance" to find relevant positions, then call get_job_details with job_index=1 to fetch the first stored job.
"""
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_jobs",
            description="Search for job listings on Stepstone.de using multiple search terms",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of job search terms to look for",
                        "default": ["fraud", "betrug", "compliance"],
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "German postal code for location-based search",
                        "default": "40210",
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in kilometers",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_job_details",
            description=(
                "Get detailed information about a specific job from stored search results. "
                "Provide job_index (1-based) to select by position or job_query to fuzzy match when no index is supplied."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from a previous search (optional; latest active session will be used if omitted)",
                    },
                    "job_query": {
                        "type": "string",
                        "description": (
                            "Job title or company name to search for in previous results. "
                            "Deprecated alias 'query' remains supported for compatibility."
                        ),
                    },
                    "job_index": {
                        "type": "integer",
                        "description": "Index of the job in previous results (1-based, optional)",
                        "minimum": 1,
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "search_jobs":
        # Extract parameters with defaults
        search_terms = arguments.get("search_terms", ["fraud", "betrug", "compliance"])
        zip_code = arguments.get("zip_code", "40210")
        radius = arguments.get("radius", 5)

        # Validate parameters
        if not isinstance(search_terms, list) or not search_terms:
            return [
                types.TextContent(
                    type="text",
                    text="Error: search_terms must be a non-empty list of strings",
                )
            ]

        normalized_terms: list[str] = []
        for term in search_terms:
            if not isinstance(term, str):
                return [
                    types.TextContent(
                        type="text",
                        text="Error: search_terms must contain only non-empty strings",
                    )
                ]

            stripped = term.strip()
            if not stripped:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: search_terms must contain only non-empty strings",
                    )
                ]

            normalized_terms.append(stripped)

        if not isinstance(zip_code, str) or len(zip_code) != 5 or not zip_code.isdigit():
            return [
                types.TextContent(
                    type="text",
                    text="Error: zip_code must be a 5-digit numeric German postal code string",
                )
            ]

        if not isinstance(radius, int) or radius < 1 or radius > 100:
            return [
                types.TextContent(
                    type="text",
                    text="Error: radius must be an integer between 1 and 100",
                )
            ]

        try:
            # Perform the job search without blocking the event loop
            logger.info(
                "Searching jobs with terms: %s, zip: %s, radius: %s",
                normalized_terms,
                zip_code,
                radius,
            )
            results = await asyncio.to_thread(
                scraper.search_jobs,
                normalized_terms,
                zip_code,
                radius,
            )

            # Create session for search results
            all_jobs = []
            for term, jobs in results.items():
                all_jobs.extend(jobs)

            if not all_jobs:
                logger.info(
                    "Job search returned no results for terms=%s zip=%s radius=%s",
                    search_terms,
                    zip_code,
                    radius,
                )

            session = session_manager.create_session(
                all_jobs, normalized_terms, zip_code, radius
            )

            # Format results for display
            formatted_output = []
            total_jobs = 0

            for term, jobs in results.items():
                total_jobs += len(jobs)
                formatted_output.append(f"\n--- Results for '{term}' ---")

                if not jobs:
                    formatted_output.append(
                        "No jobs found for this search term. Try refining your search terms or expanding the radius."
                    )
                else:
                    for i, job in enumerate(jobs, 1):
                        formatted_output.append(f"\n{i}. {job['title']}")
                        formatted_output.append(f"   Company: {job['company']}")
                        formatted_output.append(f"   Description: {job['description']}")
                        formatted_output.append(f"   Link: {job['link']}")

            # Add summary
            summary = f"Job Search Summary:\n"
            summary += f"Search Terms: {', '.join(normalized_terms)}\n"
            summary += f"Location: {zip_code} (±{radius}km)\n"
            summary += f"Total Jobs Found: {total_jobs}\n"
            summary += f"Session ID: {session}\n"
            if all_jobs:
                tip_example = all_jobs[0]["title"]
                summary += (
                    "\n💡 Tip: Use 'get_job_details' tool with "
                    f'job_query="{tip_example}" to get more details about any job!'
                )
            else:
                summary += (
                    "\n💡 Tip: Try adjusting your search terms or refining your search terms "
                    "for broader results."
                )

            full_response = summary + "\n".join(formatted_output)

            return [types.TextContent(type="text", text=full_response)]

        except Exception as e:
            logger.error(f"Error in search_jobs: {e}")
            return [
                types.TextContent(
                    type="text", text=f"Error performing job search: {str(e)}"
                )
            ]
    elif name == "get_job_details":
        # Extract parameters
        query = arguments.get("job_query") or arguments.get("query")
        session_id = arguments.get("session_id")
        job_index = arguments.get("job_index")

        # Validate parameters
        if job_index is not None:
            if not isinstance(job_index, int) or job_index < 1:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: job_index must be an integer greater than or equal to 1",
                    )
                ]

        if not query and job_index is None:
            return [
                types.TextContent(
                    type="text",
                    text="Error: provide either a query string or a job_index to identify the job",
                )
            ]

        try:
            # Get job details
            logger.info(
                "Getting job details with parameters: query=%s, session_id=%s, job_index=%s",
                query,
                session_id,
                job_index,
            )

            # Resolve the target session
            if session_id:
                resolved_session = session_manager.get_session(session_id)
                if not resolved_session:
                    return [
                        types.TextContent(
                            type="text",
                            text=(
                                "Session not found or expired. Please provide an active session_id or run a new job search."
                            ),
                        )
                    ]
            else:
                resolved_session = session_manager.get_recent_session()
                if not resolved_session:

                    return [
                        types.TextContent(
                            type="text",
                            text="No jobs available in the selected session. Please perform a new search.",
                        )
                    ]

            job = None

            if job_index is not None:
                job = session_manager.get_job_by_index(
                    resolved_session.session_id, job_index
                )
                if not job:
                    total_jobs = len(resolved_session.results)
                    if total_jobs:
                        hint = f"Valid job_index values are between 1 and {total_jobs}."
                    else:
                        hint = "There are no stored jobs for this session yet. Run a job search first."
                    return [
                        types.TextContent(
                            type="text",
                            text="No job found at the requested index. " + hint,
                        )
                    ]

            if job is None and query:
                job = session_manager.find_job_in_session(
                    resolved_session.session_id, query
                )
                if not job:
                    return [
                        types.TextContent(
                            type="text", text=f"No job found matching: {query}"
                        )
                    ]

            # Parse job details
            parser = JobDetailParser()
            details = await asyncio.to_thread(parser.parse_job_details, job["link"])

            if not details:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Could not retrieve details for job: {job['title']}",
                    )
                ]

            # Format detailed response
            formatted_output = []
            formatted_output.append(
                f"📋 Job Details: {str(details.title or 'Unknown Title')}"
            )
            formatted_output.append(
                f"🏢 Company: {str(details.company or 'Unknown Company')}"
            )

            if details.location:
                formatted_output.append(f"📍 Location: {str(details.location)}")

            if details.salary:
                formatted_output.append(f"💰 Salary: {str(details.salary)}")

            if details.employment_type:
                formatted_output.append(
                    f"⏰ Employment Type: {str(details.employment_type)}"
                )

            if details.posted_date:
                formatted_output.append(f"📅 Posted: {str(details.posted_date)}")

            formatted_output.append("")
            formatted_output.append("📝 Description:")
            # Ensure description is a string
            description_str = (
                str(details.description)
                if details.description
                else "No description available"
            )
            formatted_output.append(description_str)

            if details.requirements:
                formatted_output.append("")
                formatted_output.append("✅ Requirements:")
                for req in details.requirements:
                    # Ensure each requirement is a string
                    if isinstance(req, dict):
                        req_str = json.dumps(req, ensure_ascii=False)
                    elif isinstance(req, list):
                        req_str = ", ".join(str(item) for item in req)
                    else:
                        req_str = str(req) if req is not None else ""
                    formatted_output.append(f"  • {req_str}")

            if details.benefits:
                formatted_output.append("")
                formatted_output.append("🎁 Benefits:")
                for benefit in details.benefits:
                    # Ensure each benefit is a string
                    if isinstance(benefit, dict):
                        benefit_str = json.dumps(benefit, ensure_ascii=False)
                    elif isinstance(benefit, list):
                        benefit_str = ", ".join(str(item) for item in benefit)
                    else:
                        benefit_str = str(benefit) if benefit is not None else ""
                    formatted_output.append(f"  • {benefit_str}")

            if details.contact_info:
                formatted_output.append("")
                formatted_output.append("📞 Contact:")
                if isinstance(details.contact_info, dict):
                    contact_str = json.dumps(details.contact_info, ensure_ascii=False)
                elif isinstance(details.contact_info, list):
                    contact_str = ", ".join(str(item) for item in details.contact_info)
                else:
                    contact_str = (
                        str(details.contact_info)
                        if details.contact_info
                        else "No contact information available"
                    )
                formatted_output.append(contact_str)

            formatted_output.append("")
            apply_url = str(details.job_url or job["link"])
            formatted_output.append(f"🔗 Apply: {apply_url}")

            return [types.TextContent(type="text", text="\n".join(formatted_output))]

        except Exception as e:
            logger.error(f"Error in get_job_details: {e}")
            return [
                types.TextContent(
                    type="text", text=f"Error retrieving job details: {str(e)}"
                )
            ]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the server"""
    # Server options
    options = InitializationOptions(
        server_name="stepstone-job-search",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options,
        )


if __name__ == "__main__":
    asyncio.run(main())
