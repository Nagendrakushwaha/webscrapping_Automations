from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class BraveAdapter(BaseAdapter):
    """
    Brave Search API Adapter.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="brave", api_key=api_key, extra_config=extra_config)
        self.endpoint = "https://api.search.brave.com/res/v1/web/search"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Brave Search API key is not configured."
        try:
            headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}
            params = {"q": "Tex Web Solutions", "count": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                if resp.status_code == 200:
                    return True, "Brave Search API connection successful!"
                return False, f"Brave API error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Brave connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}
            params = {"q": query, "count": max_results}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("web", {}).get("results", []):
                        results.append(SearchResultItem(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("description", ""),
                            source_name="Brave Search"
                        ))
                    return results
        except Exception:
            return []
        return []
