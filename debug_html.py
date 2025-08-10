#!/usr/bin/env python3
"""
Debug script to analyze Stepstone HTML structure
"""

import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def debug_stepstone_html():
    """Debug the HTML structure to understand job link extraction"""
    
    # Test URL
    url = "https://www.stepstone.de/jobs/software-engineer/in-40210?radius=10&searchOrigin=Homepage_top-search&q=%22software-engineer%22"
    
    print("Fetching URL:", url)
    response = requests.get(url, headers=headers, timeout=10)
    print("Status:", response.status_code)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Save HTML for inspection
    with open('stepstone_debug.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("\n=== Looking for job containers ===")
    container = soup.find('div', id='app-unifiedResultlist')
    if container:
        print("Found job container")
    else:
        print("No job container found")
        return
    
    print("\n=== Looking for job articles ===")
    articles = container.find_all('article', attrs={'data-testid': 'job-item'})
    print(f"Found {len(articles)} job articles")
    
    for i, article in enumerate(articles[:3]):  # First 3 articles
        print(f"\n--- Article {i+1} ---")
        
        # Find all links
        all_links = article.find_all('a', href=True)
        print(f"Found {len(all_links)} links:")
        
        for j, link in enumerate(all_links):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]
            print(f"  Link {j+1}: href='{href}' text='{text}'")
        
        # Look for specific patterns
        print("Looking for job posting patterns:")
        job_links = [a for a in all_links if re.search(r'/stellenangebote--.*--\d+-inline\.html', a.get('href', ''))]
        print(f"Found {len(job_links)} job posting links")
        
        for jl in job_links:
            print(f"  Job link: {jl.get('href')}")
        
        # Look for company links
        company_links = [a for a in all_links if '/cmp/' in a.get('href', '')]
        print(f"Found {len(company_links)} company links")
        for cl in company_links:
            print(f"  Company link: {cl.get('href')}")

if __name__ == "__main__":
    debug_stepstone_html()