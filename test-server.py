#!/usr/bin/env python3
"""
Test script to verify the MCP server functionality
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import requests
        import bs4
        import mcp
        from stepstone_server import StepstoneJobScraper
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_scraper():
    """Test the scraper functionality"""
    try:
        scraper = StepstoneJobScraper()
        url = scraper.build_search_url("python developer", "10115", 10)
        print(f"✓ URL generation works: {url}")
        return True
    except Exception as e:
        print(f"✗ Scraper error: {e}")
        return False

if __name__ == "__main__":
    print("Testing MCP Stepstone Server...")
    
    success = True
    success &= test_imports()
    success &= test_scraper()
    
    if success:
        print("\n✓ All tests passed - Server is ready for deployment")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)