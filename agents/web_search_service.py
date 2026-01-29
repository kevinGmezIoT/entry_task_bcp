import os
import logging
from typing import List, Dict, Any
from tavily import TavilyClient

logger = logging.getLogger("agents-flask.web_search")

class TavilyWebSearchService:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        
        # Governance: Allowlist of domains
        self.allowlist = [
            "bcp.com.pe",
            "elcomercio.pe",
            "gestion.pe",
            "rpp.pe",
            "andina.pe",
            "infobae.com",
            "bloomberg.com",
            "reuters.com",
            "threatpost.com",
            "darkreading.com"
        ]
        
        # Simple in-memory cache
        self._cache = {}

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Performs a governed web search using Tavily.
        """
        if not self.api_key or self.api_key == "your_tavily_api_key_here":
            logger.warning("TAVILY_API_KEY not set or invalid. Returning mock data.")
            return [
                {
                    "url": "https://mock-intel.bcp.com.pe/alerts/M-002",
                    "summary": f"Mock threat intelligence for: {query}. (Tavily API Key missing)",
                    "source": "MockIntel",
                    "timestamp": "2026-01-28"
                }
            ]

        # Check Cache
        if query in self._cache:
            logger.info(f"Returning cached results for: {query}")
            return self._cache[query]

        try:
            logger.info(f"Performing Tavily search for: {query}")
            # we limit search to the allowlist using the 'include_domains' parameter if needed, 
            # but for a broader 'Threat Intel' we might just filter or let it be.
            # Tavily handles the 'intelligence' part well.
            response = self.client.search(
                query=query, 
                search_depth="advanced", 
                max_results=max_results,
                include_domains=self.allowlist # Apply governance
            )

            results = []
            for result in response.get('results', []):
                results.append({
                    "url": result.get('url'),
                    "summary": result.get('content'),
                    "source": result.get('url').split('/')[2], # Simple domain extractor
                    "timestamp": "2026-01-28" # Tavily doesn't always return a TS per result
                })
            
            # Save to cache
            self._cache[query] = results
            return results

        except Exception as e:
            logger.error(f"Error performing Tavily search: {str(e)}")
            return []

# Singleton instance
web_search_service = TavilyWebSearchService()
