from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class BingAdapter(BaseAdapter):
    """
    Microsoft Bing Web Search API v7 Adapter.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="bing", api_key=api_key, extra_config=extra_config)
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Bing Search API key is not configured."
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": "Tex Web Solutions", "count": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                if resp.status_code == 200:
                    return True, "Bing Search API connection successful!"
                return False, f"Bing API error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Bing connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "count": max_results}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("webPages", {}).get("value", []):
                        results.append(SearchResultItem(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source_name="Bing Search"
                        ))
                    return results
        except Exception:
            return []
        return []
