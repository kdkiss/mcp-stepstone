#!/usr/bin/env python3
"""
Simple health check script for the Stepstone MCP server
"""

import sys
import json

def health_check():
    """Basic health check"""
    try:
        # Import main modules to verify they work
        import requests
        import bs4
        import mcp
        
        return {
            "status": "healthy",
            "service": "stepstone-job-search",
            "version": "1.0.0"
        }
    except ImportError as e:
        return {
            "status": "unhealthy",
            "error": f"Missing dependency: {e}"
        }

if __name__ == "__main__":
    result = health_check()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "healthy" else 1)