#!/usr/bin/env python3
"""
Job detail parser for extracting comprehensive information from Stepstone job pages
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import requests
from job_details_models import JobDetails, PageParseError, NetworkError

logger = logging.getLogger("stepstone-server")

class JobDetailParser:
    """Parser for extracting detailed job information from Stepstone job pages"""
    
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def fetch_job_page(self, url: str) -> str:
        """Fetch the HTML content of a job page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Network error fetching job page {url}: {e}")
            raise NetworkError(f"Failed to fetch job page: {str(e)}")
    
    def parse_job_details(self, url: str) -> JobDetails:
        """Parse comprehensive job details from a Stepstone job page"""
        try:
            logger.info(f"Starting to parse job details from URL: {url}")
            html_content = self.fetch_job_page(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            logger.debug("Successfully fetched and parsed HTML content")
            
            # Extract basic information
            logger.debug("Extracting basic job information...")
            title = self._extract_title(soup)
            logger.debug(f"Title extracted: {title}")
            
            company = self._extract_company(soup)
            logger.debug(f"Company extracted: {company}")
            
            location = self._extract_location(soup)
            logger.debug(f"Location extracted: {location}")
            
            salary = self._extract_salary(soup)
            logger.debug(f"Salary extracted: {salary}")
            
            employment_type = self._extract_employment_type(soup)
            logger.debug(f"Employment type extracted: {employment_type}")
            
            experience_level = self._extract_experience_level(soup)
            logger.debug(f"Experience level extracted: {experience_level}")
            
            posted_date = self._extract_posted_date(soup)
            logger.debug(f"Posted date extracted: {posted_date}")
            
            # Extract detailed content
            logger.debug("Extracting detailed content...")
            description = self._extract_description(soup)
            logger.debug(f"Description length: {len(description)} chars")
            
            requirements = self._extract_requirements(soup)
            logger.debug(f"Requirements extracted: {len(requirements)} items")
            
            responsibilities = self._extract_responsibilities(soup)
            logger.debug(f"Responsibilities extracted: {len(responsibilities)} items")
            
            benefits = self._extract_benefits(soup)
            logger.debug(f"Benefits extracted: {len(benefits)} items")
            
            # Extract company and application information
            logger.debug("Extracting company and application information...")
            company_details = self._extract_company_details(soup)
            logger.debug(f"Company details extracted: {company_details}")
            
            application_instructions = self._extract_application_instructions(soup)
            logger.debug(f"Application instructions extracted: {len(application_instructions)} chars")
            
            contact_info = self._extract_contact_info(soup)
            logger.debug(f"Contact info extracted: {contact_info}")
            
            # Validate all data types before creating JobDetails
            logger.debug("Validating extracted data types...")
            job_details_data = {
                "title": str(title),
                "company": str(company),
                "location": str(location),
                "salary": str(salary) if salary else None,
                "employment_type": str(employment_type) if employment_type else None,
                "experience_level": str(experience_level) if experience_level else None,
                "posted_date": str(posted_date) if posted_date else None,
                "description": str(description),
                "requirements": [str(r) for r in requirements],
                "responsibilities": [str(r) for r in responsibilities],
                "benefits": [str(b) for b in benefits],
                "company_details": {str(k): str(v) for k, v in company_details.items()},
                "application_instructions": str(application_instructions),
                "contact_info": {str(k): str(v) for k, v in contact_info.items()},
                "job_url": str(url)
            }
            
            logger.info("All data validated, creating JobDetails object")
            return JobDetails(**job_details_data)
            
        except Exception as e:
            logger.error(f"Error parsing job details from {url}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise PageParseError(f"Failed to parse job details: {str(e)}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title"""
        title_selectors = [
            'h1[data-testid="job-title"]',
            'h1[class*="job-title"]',
            'h1[class*="JobTitle"]',
            'h1[class*="title"]',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return "Unknown Title"
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name"""
        company_selectors = [
            '[data-testid="company-name"]',
            '[class*="company-name"]',
            '[class*="CompanyName"]',
            'a[href*="/cmp/"]',
            'h2[class*="company"]'
        ]
        
        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                return company_elem.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract job location"""
        location_selectors = [
            '[data-testid="job-location"]',
            '[class*="job-location"]',
            '[class*="JobLocation"]',
            '[class*="location"]'
        ]
        
        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem:
                return location_elem.get_text(strip=True)
        
        return "Location not specified"
    
    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary information"""
        salary_selectors = [
            '[data-testid="salary"]',
            '[class*="salary"]',
            '[class*="Salary"]',
            'div:contains("€")',
            'span:contains("€")'
        ]
        
        for selector in salary_selectors:
            salary_elem = soup.select_one(selector)
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                if '€' in salary_text or 'Gehalt' in salary_text.lower():
                    return salary_text
        
        # Try regex for salary patterns
        salary_pattern = r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€(?:\s*(?:pro\s*(?:Monat|Jahr)|p\.?\s*a\.?|p\.?\s*m\.?))?)'
        text_content = soup.get_text()
        match = re.search(salary_pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_employment_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract employment type (full-time, part-time, etc.)"""
        type_selectors = [
            '[data-testid="employment-type"]',
            '[class*="employment-type"]',
            '[class*="EmploymentType"]'
        ]
        
        for selector in type_selectors:
            type_elem = soup.select_one(selector)
            if type_elem:
                return type_elem.get_text(strip=True)
        
        # Try to find in text
        text = soup.get_text().lower()
        employment_types = ['vollzeit', 'teilzeit', 'befristet', 'unbefristet', 'freelance', 'praktikum', 'werkstudent']
        for emp_type in employment_types:
            if emp_type in text:
                return emp_type.capitalize()
        
        return None
    
    def _extract_experience_level(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract required experience level"""
        experience_selectors = [
            '[data-testid="experience-level"]',
            '[class*="experience-level"]',
            '[class*="ExperienceLevel"]'
        ]
        
        for selector in experience_selectors:
            exp_elem = soup.select_one(selector)
            if exp_elem:
                return exp_elem.get_text(strip=True)
        
        # Try to find in text
        text = soup.get_text().lower()
        experience_levels = ['einsteiger', 'berufserfahren', 'senior', 'leitung', 'fachkraft']
        for level in experience_levels:
            if level in text:
                return level.capitalize()
        
        return None
    
    def _extract_posted_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract when the job was posted"""
        date_selectors = [
            '[data-testid="posted-date"]',
            '[class*="posted-date"]',
            '[class*="PostedDate"]',
            '[class*="date-posted"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                return date_elem.get_text(strip=True)
        
        # Try to find date patterns in text
        text = soup.get_text()
        date_patterns = [
            r'vor\s+(\d+)\s+(Tag|Tage|Stunde|Stunden|Minute|Minuten)',
            r'(\d{1,2}\.\d{1,2}\.\d{4})',
            r'(\d{2}/\d{2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract main job description"""
        description_selectors = [
            '[data-testid="job-description"]',
            '[class*="job-description"]',
            '[class*="JobDescription"]',
            'div[class*="description"]',
            'section[class*="description"]'
        ]
        
        for selector in description_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(strip=True, separator='\n')
        
        # Fallback: try to find the main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main'))
        if main_content:
            return main_content.get_text(strip=True, separator='\n')[:2000] + "..."
        
        return "Description not available"
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements sections
        req_selectors = [
            '[data-testid="requirements"]',
            '[class*="requirements"]',
            '[class*="Requirements"]',
            'h3:contains("Anforderungen")',
            'h3:contains("Requirements")',
            'h2:contains("Anforderungen")',
            'h2:contains("Requirements")'
        ]
        
        for selector in req_selectors:
            req_section = soup.select_one(selector)
            if req_section:
                # Find lists within requirements section
                lists = req_section.find_all(['ul', 'ol'])
                if not lists:
                    # Look for sibling lists
                    lists = req_section.find_next_siblings(['ul', 'ol'])
                
                for lst in lists:
                    items = lst.find_all('li')
                    requirements.extend([item.get_text(strip=True) for item in items])
                
                if requirements:
                    break
        
        return requirements
    
    def _extract_responsibilities(self, soup: BeautifulSoup) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for responsibilities sections
        resp_selectors = [
            '[data-testid="responsibilities"]',
            '[class*="responsibilities"]',
            '[class*="Responsibilities"]',
            'h3:contains("Aufgaben")',
            'h3:contains("Responsibilities")',
            'h2:contains("Aufgaben")',
            'h2:contains("Responsibilities")'
        ]
        
        for selector in resp_selectors:
            resp_section = soup.select_one(selector)
            if resp_section:
                # Find lists within responsibilities section
                lists = resp_section.find_all(['ul', 'ol'])
                if not lists:
                    # Look for sibling lists
                    lists = resp_section.find_next_siblings(['ul', 'ol'])
                
                for lst in lists:
                    items = lst.find_all('li')
                    responsibilities.extend([item.get_text(strip=True) for item in items])
                
                if responsibilities:
                    break
        
        return responsibilities
    
    def _extract_benefits(self, soup: BeautifulSoup) -> List[str]:
        """Extract job benefits"""
        benefits = []
        
        # Look for benefits sections
        benefits_selectors = [
            '[data-testid="benefits"]',
            '[class*="benefits"]',
            '[class*="Benefits"]',
            'h3:contains("Benefits")',
            'h3:contains("Leistungen")',
            'h2:contains("Benefits")',
            'h2:contains("Leistungen")'
        ]
        
        for selector in benefits_selectors:
            benefits_section = soup.select_one(selector)
            if benefits_section:
                # Find lists within benefits section
                lists = benefits_section.find_all(['ul', 'ol'])
                if not lists:
                    # Look for sibling lists
                    lists = benefits_section.find_next_siblings(['ul', 'ol'])
                
                for lst in lists:
                    items = lst.find_all('li')
                    benefits.extend([item.get_text(strip=True) for item in items])
                
                if benefits:
                    break
        
        return benefits
    
    def _extract_company_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract company information"""
        company_details = {}
        
        # Company description
        company_desc_selectors = [
            '[data-testid="company-description"]',
            '[class*="company-description"]',
            '[class*="CompanyDescription"]'
        ]
        
        for selector in company_desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                company_details['description'] = desc_elem.get_text(strip=True)
                break
        
        # Company size
        size_pattern = r'(\d+(?:-\d+)?\s*(?:Mitarbeiter|Employees))'
        text = soup.get_text()
        match = re.search(size_pattern, text, re.IGNORECASE)
        if match:
            company_details['size'] = match.group(1)
        
        # Company website
        website_elem = soup.find('a', href=re.compile(r'https?://(?!www\.stepstone\.de)'))
        if website_elem:
            company_details['website'] = website_elem['href']
        
        return company_details
    
    def _extract_application_instructions(self, soup: BeautifulSoup) -> str:
        """Extract application instructions"""
        app_selectors = [
            '[data-testid="application-instructions"]',
            '[class*="application-instructions"]',
            '[class*="ApplicationInstructions"]',
            'h3:contains("Bewerbung")',
            'h2:contains("Bewerbung")'
        ]
        
        for selector in app_selectors:
            app_section = soup.select_one(selector)
            if app_section:
                return app_section.get_text(strip=True, separator='\n')
        
        # Look for apply buttons or links
        apply_buttons = soup.find_all(['a', 'button'], string=re.compile(r'(?i)(bewerben|apply|jetzt bewerben)'))
        if apply_buttons:
            return "Click the apply button/link to submit your application"
        
        return "Application instructions not provided"
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information"""
        contact_info = {}
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone numbers (German format)
        phone_pattern = r'(?:\+49|0)[\s\-/]?[1-9]\d{1,4}[\s\-/]?\d{1,7}(?:[\s\-/]?\d{1,7})?'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # Contact person
        contact_patterns = [
            r'(?:Ansprechpartner|Kontakt|Contact):\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'(?:Frau|Herr)\s+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, text)
            if match:
                contact_info['contact_person'] = match.group(1)
                break
        
        return contact_info