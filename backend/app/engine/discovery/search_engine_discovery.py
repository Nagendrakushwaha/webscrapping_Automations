import re
from urllib.parse import unquote, urlparse
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Any
from .base import BaseDiscoveryAdapter, DiscoveredLead

PHONE_REGEX = re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')

class SearchEngineDiscoveryAdapter(BaseDiscoveryAdapter):
    """
    Search Engine & Public Business Directory Discovery Adapter.
    Uses DuckDuckGo HTML / Bing / Brave to discover companies, websites, phones, and snippets
    for targeted industry and location queries.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="search_engine", api_key=api_key, extra_config=extra_config)
        self.ddg_endpoint = "https://html.duckduckgo.com/html/"

    @property
    def is_configured(self) -> bool:
        return True

    def discover_sync(
        self,
        industry: str,
        trade: str,
        city: str,
        state: str,
        center_lat: float,
        center_lon: float,
        radius_miles: float,
        limit: int = 50
    ) -> list[DiscoveredLead]:
        leads = []
        term = trade or industry or "contractor"
        query_text = f'"{term}" "{city}" {state} official website contact'

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            with httpx.Client(timeout=8.0, headers=headers, follow_redirects=True) as client:
                resp = client.post(self.ddg_endpoint, data={"q": query_text})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("div", class_="result")

                    for r in results:
                        title_tag = r.find("a", class_="result__a")
                        snippet_tag = r.find("a", class_="result__snippet")
                        url_tag = r.find("a", class_="result__url")

                        if not title_tag:
                            continue

                        raw_title = title_tag.get_text(strip=True)
                        raw_snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        raw_href = title_tag.get("href", "")

                        # Extract clean destination URL
                        dest_url = ""
                        if "uddg=" in raw_href:
                            try:
                                dest_url = unquote(raw_href.split("uddg=")[1].split("&")[0])
                            except Exception:
                                dest_url = raw_href
                        elif raw_href.startswith("http"):
                            dest_url = raw_href

                        # Filter out social aggregates, directories, or irrelevant sites
                        parsed = urlparse(dest_url)
                        domain = parsed.netloc.lower().replace("www.", "")
                        if any(x in domain for x in ["yelp.com", "yellowpages.com", "angi.com", "homeadvisor.com", "thumbtack.com", "bbb.org", "wikipedia.org", "duckduckgo.com"]):
                            continue

                        # Extract company name from title
                        clean_name = raw_title.split("-")[0].split("|")[0].split(":")[0].strip()
                        if len(clean_name) < 3 or len(clean_name) > 60:
                            continue

                        # Look for phone number in snippet
                        phone_match = PHONE_REGEX.search(raw_snippet)
                        phone = phone_match.group(0) if phone_match else ""

                        leads.append(DiscoveredLead(
                            name=clean_name,
                            industry=industry,
                            trade=trade or industry,
                            address=f"{city}, {state}",
                            city=city,
                            state=state,
                            phone=phone,
                            website=dest_url,
                            latitude=center_lat,
                            longitude=center_lon,
                            distance_miles=0.0,
                            provider="Public Web Search",
                            provider_place_id=f"web_{domain}",
                            raw_metadata={"title": raw_title, "snippet": raw_snippet}
                        ))

                        if len(leads) >= limit:
                            break
        except Exception:
            pass

        return leads
