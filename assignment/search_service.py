import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def perform_tavily_search(query, max_results=5):
    """
    Perform a search using the Tavily API.
    Returns a list of results with title, url, and content/snippet.
    """
    api_key = getattr(settings, 'TAVILY_API_KEY', None)
    if not api_key:
        logger.warning("TAVILY_API_KEY not found in settings. Falling back to mock search.")
        return mock_search(query)

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for res in data.get('results', []):
            results.append({
                'title': res.get('title', 'No Title'),
                'url': res.get('url', '#'),
                'content': res.get('content', '')
            })
        
        return {
            'results': results,
            'answer': data.get('answer', '')
        }
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return mock_search(query)

def mock_search(query):
    """Fallback mock search for testing."""
    return {
        'results': [
            {
                'title': f"Research Findings on {query}",
                'url': "https://nexa-intelligence.ai/research",
                'content': f"Detailed analysis of {query} suggests a significant correlation between initial data points and subsequent synthesis."
            },
            {
                'title': "Global Trends Report 2026",
                'url': "https://nexa-trends.io",
                'content': "Autonomous agents are increasingly used for deep research and information retrieval in academic environments."
            }
        ],
        'answer': f"Based on current NEXA intelligence, {query} is a multifaceted topic requiring deep synthesis."
    }

def generate_research_queries(prompt):
    """
    Use AI to generate 3 focused search queries for the deep research phase.
    """
    from .ai_utils import get_openai_client
    try:
        client = get_openai_client()
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate 3 specific, search-optimized queries to research the following assignment prompt. Output only the queries, one per line."},
                {"role": "user", "content": prompt}
            ]
        )
        queries = resp.choices[0].message.content.strip().split('\n')
        return [q.strip('- ').strip() for q in queries if q.strip()][:3]
    except Exception as e:
        logger.error(f"Query generation error: {e}")
        return [prompt]
