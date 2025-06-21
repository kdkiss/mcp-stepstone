#!/usr/bin/env python3
from jsonrpcserver import method, serve
import json
from job_fetcher import fetch_job_listings, build_url

DEFAULT_TERMS = ["fraud", "crime", "betrug", "fraud_specialist"]
DEFAULT_ZIP = "40210"
DEFAULT_RADIUS = 5

@method
def initialize(params=None):
    return {"status": "initialized"}

@method
def tools__list(params=None):
    return [{
        "name": "fetch_jobs",
        "description": "Fetch job listings from Stepstone.de",
        "parameters": {
            "type": "object",
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords"
                },
                "zip_code": {"type": "string", "description": "ZIP code"},
                "radius": {"type": "integer", "description": "Radius (km)"}
            }
        }
    }]

@method
def tools__call(params):
    if params["name"] != "fetch_jobs":
        return {"error": "Unknown tool"}
    args = params.get("args", {})
    terms = args.get("search_terms", DEFAULT_TERMS)
    zip_code = args.get("zip_code", DEFAULT_ZIP)
    radius = args.get("radius", DEFAULT_RADIUS)

    results = {}
    for term in terms:
        url = build_url(term, zip_code, radius)
        jobs = fetch_job_listings(url)
        results[term] = jobs
    return {"results": results}

if __name__ == "__main__":
    serve()