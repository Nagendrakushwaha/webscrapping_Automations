from typing import Optional, Any
from urllib.parse import unquote
import httpx
from bs4 import BeautifulSoup
from .base import BaseAdapter, SearchResultItem
from ...config import settings

class DuckDuckGoAdapter(BaseAdapter):
    """
    Direct DuckDuckGo Web Search Adapter (HTML fallback).
    Works without any API key, adhering to polite timeouts and standard headers.
    """
    def __init__(self, api_key: str = "free", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="duckduckgo", api_key="free", extra_config=extra_config)
        self.endpoint = "https://html.duckduckgo.com/html/"

    @property
    def is_configured(self) -> bool:
        return True

    async def test_connection(self) -> tuple[bool, str]:
        return True, "DuckDuckGo search adapter is ready (no API key required)."

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://duckduckgo.com/"
        }
        data = {"q": query, "b": ""}
        results = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                resp = await client.post(self.endpoint, data=data)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("div", class_="result", limit=max_results)
                    for lk in links:
                        title_tag = lk.find("a", class_="result__a")
                        snippet_tag = lk.find("a", class_="result__snippet")
                        if not title_tag:
                            continue
                        raw_href = title_tag.get("href", "")
                        # Duckduckgo wraps URL in /l/?uddg=...
                        final_url = raw_href
                        if "uddg=" in raw_href:
                            try:
                                final_url = unquote(raw_href.split("uddg=")[1].split("&")[0])
                            except Exception:
                                final_url = raw_href

                        title = title_tag.get_text(strip=True)
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        
                        results.append(SearchResultItem(
                            title=title,
                            url=final_url,
                            snippet=snippet,
                            source_name="DuckDuckGo"
                        ))
        except Exception:
            pass
        return results
