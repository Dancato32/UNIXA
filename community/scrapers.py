import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import random


class ClutchAIScraper:
    """
    Scraper service for Clutch AI to discover student opportunities.
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }

    @staticmethod
    def _strip_html(raw_html):
        """Strip all HTML tags and clean up whitespace from a string."""
        if not raw_html:
            return ''
        # Parse with BeautifulSoup to safely extract text
        soup = BeautifulSoup(raw_html, 'html.parser')
        text = soup.get_text(separator=' ')
        # Collapse excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def fetch_all(self):
        """
        Aggregates results from multiple live sources.
        """
        results = []
        results.extend(self.scrape_remoteok())
        results.extend(self.scrape_hn_jobs())
        
        # Shuffle to mix sources
        random.shuffle(results)
        return results

    def scrape_remoteok(self):
        """
        Fetch live jobs from the RemoteOK API.
        """
        jobs = []
        try:
            url = "https://remoteok.com/api"
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for item in data[1:]:
                    raw_desc = item.get('description', '')
                    clean_desc = self._strip_html(raw_desc)
                    if len(clean_desc) > 400:
                        clean_desc = clean_desc[:400].rsplit(' ', 1)[0] + '...'

                    jobs.append({
                        'title': item.get('position', 'Untitled Role'),
                        'description': clean_desc,
                        'category': item.get('tags', ['Technology'])[0].capitalize(),
                        'location': item.get('location') or 'Remote',
                        'deadline': 'As soon as possible',
                        'url': item.get('url'),
                        'tags': ['#' + t for t in item.get('tags', [])[:3]] + ['#remote'],
                        'image_url': item.get('logo'),
                    })
        except Exception as e:
            print(f"Error fetching from RemoteOK: {e}")
        return jobs

    def scrape_hn_jobs(self):
        """
        Fetch newest jobs from Hacker News via Algolia API.
        """
        jobs = []
        try:
            # specifically jobs tags
            url = "https://hn.algolia.com/api/v1/search_by_date?tags=job"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                hits = response.json().get('hits', [])
                for hit in hits:
                    title = hit.get('title', 'Engineering Role')
                    # HN jobs often have 'is hiring' or details in title
                    url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                    
                    # Estimate category
                    category = "Technology"
                    if "intern" in title.lower(): category = "Internship"
                    
                    jobs.append({
                        'title': title,
                        'description': "Fresh opportunity from the Hacker News community.",
                        'category': category,
                        'location': "Varies / Remote",
                        'deadline': "Open",
                        'url': url,
                        'tags': ["#hacker-news", "#startup", "#growth"],
                        'image_url': None, # HN doesn't have logos
                    })
        except Exception as e:
            print(f"Error fetching from HN: {e}")
        return jobs
