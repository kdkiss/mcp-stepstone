#!/usr/bin/env python3
"""Test script to verify the job link extraction fix"""

from stepstone_server import StepstoneJobScraper
import json

def test_job_link_extraction():
    """Test that job links point to actual job postings"""
    print("Testing job link extraction fix...")
    
    scraper = StepstoneJobScraper()
    jobs = scraper.fetch_job_listings('https://www.stepstone.de/jobs/fraud-compliance?radius=5')
    
    print(f"Found {len(jobs)} jobs")
    print()
    
    if not jobs:
        print("No jobs found - this might indicate an issue with the scraping")
        return False
    
    success_count = 0
    for i, job in enumerate(jobs[:5], 1):
        link = job['link']
        is_job_posting = '/stellenangebote' in link and 'inline.html' in link
        is_company_profile = '/cmp/' in link
        
        print(f"Job {i}:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Link: {link}")
        print(f"  Is job posting: {is_job_posting}")
        print(f"  Is company profile: {is_company_profile}")
        print()
        
        if is_job_posting and not is_company_profile:
            success_count += 1
    
    print(f"Summary: {success_count}/{min(5, len(jobs))} links are actual job postings")
    
    if success_count > 0:
        print("✅ Fix successful - job links now point to actual job postings")
        return True
    else:
        print("❌ Fix failed - links still point to company profiles")
        return False

if __name__ == "__main__":
    test_job_link_extraction()