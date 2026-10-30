from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class GooglePlacesAdapter(BaseAdapter):
    """
    Google Places API Adapter for authentic business identity, address, phone, and verification.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="google_places", api_key=api_key, extra_config=extra_config)
        self.endpoint_text_search = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.endpoint_details = "https://maps.googleapis.com/maps/api/place/details/json"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Google Places API key is not configured."
        try:
            params = {"key": self.api_key, "query": "roofing contractors"}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint_text_search, params=params)
                if resp.status_code == 200:
                    status = resp.json().get("status")
                    if status in ["OK", "ZERO_RESULTS"]:
                        return True, "Google Places API connection successful!"
                    else:
                        return False, f"Google Places API status: {status}"
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Google Places failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            params = {"key": self.api_key, "query": query}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint_text_search, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for place in data.get("results", [])[:max_results]:
                        place_id = place.get("place_id")
                        title = place.get("name", "")
                        addr = place.get("formatted_address", "")
                        results.append(SearchResultItem(
                            title=title,
                            url=f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                            snippet=f"Address: {addr} | Rating: {place.get('rating', 'N/A')}",
                            source_name="Google Places",
                            extra={"place_id": place_id, "address": addr}
                        ))
                    return results
        except Exception:
            return []
        return []

    async def get_details(self, place_id: str) -> dict[str, Any]:
        if not self.is_configured or not place_id:
            return {}
        try:
            params = {
                "key": self.api_key,
                "place_id": place_id,
                "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address"
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint_details, params=params)
                if resp.status_code == 200:
                    return resp.json().get("result", {})
        except Exception:
            pass
        return {}

