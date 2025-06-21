import sys
import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

def fetch_job_listings(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        container = soup.find('div', id='app-unifiedResultlist')
        if not container:
            return []
        jobs = []
        seen = set()
        for article in container.find_all('article', attrs={'data-testid': 'job-item'}):
            a = article.find('a')
            if not a:
                continue
            title = a.text.strip()
            link = a['href']
            if not link.startswith("http"):
                link = f"https://www.stepstone.de{link}"
            if link in seen:
                continue
            seen.add(link)
            company = article.find('span', class_=re.compile('res-1bl90s9|company'))
            location = article.find('span', class_=re.compile('res-skl634|location'))
            jobs.append({
                "title": title,
                "company": company.text.strip() if company else "Unknown Company",
                "location": location.text.strip() if location else "Unknown Location",
                "link": link
            })
        return jobs
    except Exception:
        return []

def build_url(term, zip_code, radius):
    q = quote(term)
    return f"https://www.stepstone.de/jobs/{q}/in-{zip_code}?radius={radius}&searchOrigin=Homepage_top-search&q=%22{q}%22"

def main():
    data = json.load(sys.stdin)
    terms = data.get("search_terms", ["fraud", "crime", "betrug", "fraud_specialist"])
    zip_code = data.get("zip_code", "40210")
    radius = data.get("radius", 5)

    results = {}
    for term in terms:
        url = build_url(term, zip_code, radius)
        jobs = fetch_job_listings(url)
        results[term] = jobs

    json.dump({"results": results}, sys.stdout)

if __name__ == "__main__":
    main()