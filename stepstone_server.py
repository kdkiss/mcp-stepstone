#!/usr/bin/env python3
"""
Stepstone Job Search MCP Server

A Model Context Protocol server for searching job listings on Stepstone.de
Compatible with Smithery and other MCP clients.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stepstone-server")

class StepstoneJobScraper:
    """Job scraper for Stepstone.de"""
    
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def fetch_job_listings(self, url: str) -> List[Dict[str, str]]:
        """Fetch job listings from a Stepstone URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            container = soup.find('div', id='app-unifiedResultlist')
            
            if not container:
                logger.warning(f"No job container found for URL: {url}")
                return []
            
            jobs = []
            seen_links = set()
            
            for article in container.find_all('article', attrs={'data-testid': 'job-item'}):
                job_link = article.find('a')
                if not job_link:
                    continue
                
                # Extract job title from the link text or h2 element
                title_elem = article.find('h2') or job_link
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                link = job_link['href']
                
                # Ensure absolute URL
                if not link.startswith("http"):
                    link = f"https://www.stepstone.de{link}"
                
                # Skip duplicates
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                # Extract company information
                company_elem = article.find('span', class_=re.compile('res-1bl90s9|company')) or article.find('a', attrs={'data-testid': 'company-name'})
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                
                # Extract short description
                desc_elem = article.find('p', class_=re.compile('description|snippet')) or article.find('div', class_=re.compile('description|snippet'))
                description = desc_elem.get_text(strip=True)[:200] + "..." if desc_elem and desc_elem.get_text(strip=True) else "No description available"
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "description": description,
                    "link": link
                })
            
            logger.info(f"Found {len(jobs)} jobs for URL: {url}")
            return jobs
            
        except requests.RequestException as e:
            logger.error(f"Request failed for URL {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping URL {url}: {e}")
            return []
    
    def build_search_url(self, term: str, zip_code: str = "40210", radius: int = 5) -> str:
        """Build Stepstone search URL"""
        encoded_term = quote(term)
        return f"https://www.stepstone.de/jobs/{encoded_term}/in-{zip_code}?radius={radius}&searchOrigin=Homepage_top-search&q=%22{encoded_term}%22"
    
    def search_jobs(self, search_terms: List[str], zip_code: str = "40210", radius: int = 5) -> Dict[str, List[Dict[str, str]]]:
        """Search for jobs using multiple terms"""
        results = {}
        
        for term in search_terms:
            logger.info(f"Searching for jobs with term: {term}")
            url = self.build_search_url(term, zip_code, radius)
            jobs = self.fetch_job_listings(url)
            results[term] = jobs
        
        return results

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

Parameters:
- search_terms: List of job search terms (e.g., ["fraud", "betrug", "data analyst"])
- zip_code: German postal code for location-based search (default: "40210")
- radius: Search radius in kilometers (default: 5)

Example usage:
Use the search_jobs tool with terms like "fraud specialist", "betrug", "compliance" to find relevant positions.
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
                        "default": ["fraud", "betrug", "compliance"]
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "German postal code for location-based search",
                        "default": "40210"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in kilometers",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": []
            },
        )
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
            return [types.TextContent(
                type="text",
                text="Error: search_terms must be a non-empty list of strings"
            )]
        
        if not isinstance(zip_code, str) or len(zip_code) != 5:
            return [types.TextContent(
                type="text",
                text="Error: zip_code must be a 5-digit German postal code string"
            )]
        
        if not isinstance(radius, int) or radius < 1 or radius > 100:
            return [types.TextContent(
                type="text",
                text="Error: radius must be an integer between 1 and 100"
            )]
        
        try:
            # Perform the job search
            logger.info(f"Searching jobs with terms: {search_terms}, zip: {zip_code}, radius: {radius}")
            results = scraper.search_jobs(search_terms, zip_code, radius)
            
            # Format results for display
            formatted_output = []
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
            
            # Add summary
            summary = f"Job Search Summary:\n"
            summary += f"Search Terms: {', '.join(search_terms)}\n"
            summary += f"Location: {zip_code} (±{radius}km)\n"
            summary += f"Total Jobs Found: {total_jobs}\n"
            
            full_response = summary + "\n".join(formatted_output)
            
            return [types.TextContent(
                type="text",
                text=full_response
            )]
            
        except Exception as e:
            logger.error(f"Error in search_jobs: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error performing job search: {str(e)}"
            )]
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
