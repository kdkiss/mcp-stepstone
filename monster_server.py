#!/usr/bin/env python3
"""
Monster.com Job Search MCP Server

A Model Context Protocol server for searching job listings on Monster.com
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types

from job_details_models import JobDetails
from session_manager import session_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("monster-server")


class MonsterJobScraper:
    """Job scraper for Monster.com"""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def build_search_url(
        self, term: str, location: str, radius: int = 5, recency: Optional[str] = None
    ) -> str:
        base = "https://www.monster.com/jobs/search"
        url = (
            f"{base}?q={quote_plus(term)}&where={quote_plus(location)}&page=1&rd={radius}&so=m.h.sh"
        )
        if recency:
            url += f"&recency={quote_plus(recency)}"
        return url

    def fetch_job_listings(self, url: str) -> List[Dict[str, str]]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            container = soup.select_one("#card-scroll-container")
            if not container:
                logger.warning(f"No job container found for URL: {url}")
                return []

            jobs: List[Dict[str, str]] = []
            for article in container.find_all("article", attrs={"data-testid": "JobCard"}):
                title_elem = article.find("a", attrs={"data-testid": "jobTitle"})
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href")
                if link and link.startswith("//"):
                    link = "https:" + link
                company_elem = article.find("span", attrs={"data-testid": "company"})
                company = (
                    company_elem.get_text(strip=True)
                    if company_elem
                    else "Unknown Company"
                )
                location_elem = article.find(
                    "span", attrs={"data-testid": "jobDetailLocation"}
                )
                location = (
                    location_elem.get_text(strip=True)
                    if location_elem
                    else "Unknown Location"
                )
                date_elem = article.find(
                    "span", attrs={"data-testid": "jobDetailDateRecency"}
                )
                description = (
                    date_elem.get_text(strip=True) if date_elem else "No description"
                )
                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "description": f"{location} - {description}",
                        "link": link,
                    }
                )
            logger.info(f"Found {len(jobs)} jobs for URL: {url}")
            return jobs
        except requests.RequestException as e:
            logger.error(f"Request failed for URL {url}: {e}")
            return []

    def search_jobs(
        self,
        search_terms: List[str],
        location: str,
        radius: int = 5,
        recency: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, str]]]:
        results: Dict[str, List[Dict[str, str]]] = {}
        for term in search_terms:
            url = self.build_search_url(term, location, radius, recency)
            jobs = self.fetch_job_listings(url)
            results[term] = jobs
        return results


class MonsterJobDetailParser:
    """Parser for extracting detailed job information from Monster.com"""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def parse_job_details(self, url: str) -> Optional[JobDetails]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            container = soup.select_one(
                "#__next > div.main-layout-styles__Layout-sc-86e48e0f-0.ceQSkJ > div.job-openings-style__SmallJobViewWrapper-sc-b9f61078-0.iWRvKv > div"
            )
            description = (
                container.get_text("\n", strip=True)
                if container
                else "No description available"
            )
            title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            company_elem = soup.find(attrs={"data-testid": "jobHeaderCompanyName"})
            company = (
                company_elem.get_text(strip=True)
                if company_elem
                else "Unknown Company"
            )
            location_elem = soup.find(attrs={"data-testid": "jobDetailLocation"})
            location = (
                location_elem.get_text(strip=True)
                if location_elem
                else "Location not specified"
            )
            return JobDetails(
                title=title,
                company=company,
                location=location,
                salary=None,
                employment_type=None,
                experience_level=None,
                posted_date=None,
                description=description,
                requirements=[],
                responsibilities=[],
                benefits=[],
                company_details={},
                application_instructions="",
                contact_info={},
                job_url=url,
            )
        except Exception as e:
            logger.error(f"Error parsing job details from {url}: {e}")
            return None


server = Server("monster-job-search")
scraper = MonsterJobScraper()


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    return [
        Resource(
            uri="monster://search-help",
            name="Monster Job Search Help",
            description="Information about how to use the Monster job search functionality",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    if uri == "monster://search-help":
        return (
            "Monster Job Search MCP Server\n\n"
            "This server allows you to search for jobs on Monster.com."
        )
    raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_jobs",
            description="Search for job listings on Monster.com using multiple search terms",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of job search terms to look for",
                        "default": ["business analyst"],
                    },
                    "location": {
                        "type": "string",
                        "description": "Location in 'City, State' format",
                        "default": "Los Angeles, CA",
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in miles",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "recency": {
                        "type": "string",
                        "description": "Optional recency filter (e.g., last+week, today)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_job_details",
            description="Get detailed information about a specific job from previous search results",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from previous search (optional, will use latest if not provided)",
                    },
                    "job_query": {
                        "type": "string",
                        "description": "Job title or description to search for in previous results",
                    },
                },
                "required": ["job_query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "search_jobs":
        search_terms = arguments.get("search_terms", ["business analyst"])
        location = arguments.get("location", "Los Angeles, CA")
        radius = arguments.get("radius", 5)
        recency = arguments.get("recency")

        if not isinstance(search_terms, list) or not search_terms:
            return [
                types.TextContent(
                    type="text",
                    text="Error: search_terms must be a non-empty list of strings",
                )
            ]

        try:
            results = scraper.search_jobs(search_terms, location, radius, recency)
            all_jobs: List[Dict[str, str]] = []
            for jobs in results.values():
                all_jobs.extend(jobs)

            session_id = session_manager.create_session(
                all_jobs, search_terms, location, radius
            )

            formatted_output: List[str] = []
            total_jobs = 0

            for term, jobs in results.items():
                total_jobs += len(jobs)
                formatted_output.append(f"\n--- Results for '{term}' ---")
                if not jobs:
                    formatted_output.append("No jobs found for this search term.")
                else:
                    for i, job in enumerate(jobs, 1):
                        formatted_output.append(f"\n{i}. {job['title']}")
                        formatted_output.append(f"   Company: {job['company']}")
                        formatted_output.append(f"   Description: {job['description']}")
                        formatted_output.append(f"   Link: {job['link']}")

            summary = "Job Search Summary:\n"
            summary += f"Search Terms: {', '.join(search_terms)}\n"
            summary += f"Location: {location} (±{radius}mi)\n"
            summary += f"Total Jobs Found: {total_jobs}\n"
            summary += f"Session ID: {session_id}\n"

            full_response = summary + "\n".join(formatted_output)
            return [types.TextContent(type="text", text=full_response)]
        except Exception as e:
            logger.error(f"Error in search_jobs: {e}")
            return [
                types.TextContent(
                    type="text", text=f"Error performing job search: {str(e)}"
                )
            ]

    if name == "get_job_details":
        job_query = arguments.get("job_query")
        session_id = arguments.get("session_id")

        if not job_query or not isinstance(job_query, str):
            return [
                types.TextContent(
                    type="text", text="Error: job_query must be a non-empty string"
                )
            ]

        try:
            if session_id:
                job = session_manager.find_job_in_session(session_id, job_query)
            else:
                recent_session = session_manager.get_recent_session()
                if not recent_session:
                    return [
                        types.TextContent(
                            type="text",
                            text="No active search session found. Please perform a job search first.",
                        )
                    ]
                job = session_manager.find_job_in_session(
                    recent_session.session_id, job_query
                )

            if not job:
                return [
                    types.TextContent(
                        type="text", text=f"No job found matching: {job_query}"
                    )
                ]

            parser = MonsterJobDetailParser()
            details = parser.parse_job_details(job["link"])
            if not details:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Could not retrieve details for job: {job['title']}",
                    )
                ]

            output_lines = [
                f"📋 Job Details: {details.title}",
                f"🏢 Company: {details.company}",
                f"📍 Location: {details.location}",
                "",
                "📝 Description:",
                details.description,
                "",
                f"🔗 Apply: {details.job_url}",
            ]
            return [types.TextContent(type="text", text="\n".join(output_lines))]
        except Exception as e:
            logger.error(f"Error in get_job_details: {e}")
            return [
                types.TextContent(
                    type="text", text=f"Error retrieving job details: {str(e)}"
                )
            ]

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    options = InitializationOptions(
        server_name="monster-job-search",
        server_version="0.1.0",
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
