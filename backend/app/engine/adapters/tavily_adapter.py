from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class TavilyAdapter(BaseAdapter):
    """
    Tavily Search API Adapter for high-accuracy AI web search and lead enrichment.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="tavily", api_key=api_key, extra_config=extra_config)
        self.endpoint = "https://api.tavily.com/search"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Tavily API key is not configured."
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    self.endpoint,
                    json={"api_key": self.api_key, "query": "Tex Web Solutions", "max_results": 1}
                )
                if resp.status_code == 200:
                    return True, "Tavily API connection successful!"
                else:
                    return False, f"Tavily API error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Tavily connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    self.endpoint,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": self.extra_config.get("search_depth", "basic"),
                        "max_results": max_results,
                        "include_answer": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("results", []):
                        results.append(SearchResultItem(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content", ""),
                            source_name="Tavily"
                        ))
                    return results
        except Exception:
            return []
        return []
