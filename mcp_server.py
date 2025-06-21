from jsonrpcserver import method, serve
import sys
import json
from job_fetcher import build_url, fetch_job_listings

@method
def initialize():
    return {
        "name": "mcp-stepstone",
        "description": "Fetch job listings from Stepstone.de",
        "version": "1.0.0"
    }

@method
def tools_list():
    return [{
        "name": "fetch_jobs",
        "description": "Fetch Stepstone job listings based on search terms, zip code, and radius",
        "parameters": {
            "type": "object",
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of search terms"
                },
                "zip_code": {
                    "type": "string",
                    "description": "German zip code"
                },
                "radius": {
                    "type": "integer",
                    "description": "Search radius in km"
                }
            }
        }
    }]

@method
def tools_call(name, arguments):
    if name != "fetch_jobs":
        return {"error": f"Unknown tool {name}"}
    
    terms = arguments.get("search_terms", ["fraud", "crime", "betrug", "fraud_specialist"])
    zip_code = arguments.get("zip_code", "40210")
    radius = arguments.get("radius", 5)

    results = {}
    for term in terms:
        url = build_url(term, zip_code, radius)
        jobs = fetch_job_listings(url)
        results[term] = jobs

    return {"results": results}

if __name__ == "__main__":
    serve()
