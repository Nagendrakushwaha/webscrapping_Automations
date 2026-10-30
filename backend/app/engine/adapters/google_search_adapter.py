from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class GoogleSearchAdapter(BaseAdapter):
    """
    Google Custom Search JSON API Adapter.
    Requires Google Cloud API Key and Search Engine ID (cx).
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="google_search", api_key=api_key, extra_config=extra_config)
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.strip()) and bool(self.extra_config.get("cx", "").strip())

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Google Search requires both API Key and Search Engine ID (cx)."
        try:
            cx = self.extra_config.get("cx", "").strip()
            params = {"key": self.api_key, "cx": cx, "q": "test", "num": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    return True, "Google Custom Search connection successful!"
                else:
                    return False, f"Google Search error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Google Search connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            cx = self.extra_config.get("cx", "").strip()
            params = {"key": self.api_key, "cx": cx, "q": query, "num": min(max_results, 10)}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("items", []):
                        results.append(SearchResultItem(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source_name="Google Search"
                        ))
                    return results
        except Exception:
            return []
        return []

