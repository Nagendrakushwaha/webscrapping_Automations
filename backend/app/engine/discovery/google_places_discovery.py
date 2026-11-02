import time
import httpx
from typing import Optional, Any
from .base import BaseDiscoveryAdapter, DiscoveredLead
from ...core.location_service import LocationService

class GooglePlacesDiscoveryAdapter(BaseDiscoveryAdapter):
    """
    Google Places API Business Discovery Adapter.
    Executes Text Search and Nearby Search, respects the 50,000m circle limit via zone tiling,
    handles next_page_token pagination, fetches Place Details for Phone & Official Website,
    deduplicates place_ids across overlapping zones, and filters out closed businesses.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="google_places", api_key=api_key, extra_config=extra_config)
        self.text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def fetch_place_details_sync(self, client: httpx.Client, place_id: str) -> dict[str, Any]:
        """
        Fetches official phone number, website URL, and verified operational status for a place.
        Uses precise field masking to minimize Google Cloud API billing costs.
        """
        if not place_id or not self.is_configured:
            return {}

        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,international_phone_number,website,business_status,formatted_address",
            "key": self.api_key
        }

        try:
            resp = client.get(self.details_url, params=params, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("result", {})
        except Exception:
            pass

        return {}

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
        if not self.is_configured:
            return []

        leads: list[DiscoveredLead] = []
        seen_place_ids: set[str] = set()

        zones = LocationService.generate_search_zones(center_lat, center_lon, radius_miles)
        term = trade or industry or "contractor"
        query_text = f"{term} in {city}, {state}"

        with httpx.Client(timeout=10.0) as client:
            for zone in zones:
                if len(leads) >= limit:
                    break

                params = {
                    "query": query_text,
                    "location": f"{zone['center_lat']},{zone['center_lon']}",
                    "radius": int(zone["radius_meters"]),
                    "key": self.api_key
                }

                page_token = None
                pages_fetched = 0

                while pages_fetched < 3 and len(leads) < limit:
                    if page_token:
                        params = {"pagetoken": page_token, "key": self.api_key}
                        # Google Places requires brief pause before next_page_token activates
                        time.sleep(1.8)

                    try:
                        resp = client.get(self.text_search_url, params=params)
                        if resp.status_code != 200:
                            break

                        data = resp.json()
                        results = data.get("results", [])
                        if not results:
                            break

                        for place in results:
                            place_id = place.get("place_id", "")
                            if not place_id or place_id in seen_place_ids:
                                continue

                            # 1. Filter out permanently or temporarily closed businesses
                            status = place.get("business_status", "OPERATIONAL").upper()
                            if status in ["CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"]:
                                seen_place_ids.add(place_id)
                                continue

                            # 2. Strict radius distance verification
                            geom = place.get("geometry", {}).get("location", {})
                            plat = geom.get("lat")
                            plon = geom.get("lng")

                            dist_miles = 0.0
                            if plat and plon:
                                is_inside, dist_miles = LocationService.is_within_radius(
                                    center_lat, center_lon, plat, plon, radius_miles
                                )
                                if not is_inside:
                                    continue

                            seen_place_ids.add(place_id)

                            # 3. Retrieve Place Details for Phone & Official Website
                            details = self.fetch_place_details_sync(client, place_id)

                            # Re-verify business_status if details provides newer info
                            detail_status = details.get("business_status", "").upper()
                            if detail_status in ["CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"]:
                                continue

                            phone = details.get("formatted_phone_number") or details.get("international_phone_number") or ""
                            website = details.get("website") or ""
                            formatted_addr = details.get("formatted_address") or place.get("formatted_address") or place.get("vicinity", "")

                            name = place.get("name", "")

                            raw_meta = {
                                **place,
                                "details": details
                            }

                            leads.append(DiscoveredLead(
                                name=name,
                                industry=industry,
                                trade=trade or industry,
                                address=formatted_addr,
                                city=city,
                                state=state,
                                phone=phone,
                                website=website,
                                latitude=plat,
                                longitude=plon,
                                distance_miles=dist_miles,
                                provider="Google Places API",
                                provider_place_id=place_id,
                                rating=place.get("rating"),
                                reviews_count=place.get("user_ratings_total"),
                                raw_metadata=raw_meta
                            ))

                            if len(leads) >= limit:
                                break

                        page_token = data.get("next_page_token")
                        pages_fetched += 1
                        if not page_token:
                            break

                    except Exception:
                        break

        return leads
