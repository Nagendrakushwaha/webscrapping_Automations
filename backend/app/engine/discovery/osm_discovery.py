import re
import httpx
from typing import Optional, Any
from .base import BaseDiscoveryAdapter, DiscoveredLead
from ...core.location_service import LocationService

INDUSTRY_OSM_TAG_MAPPING = {
    "roofing": '["craft"="roofer"]',
    "construction": '["building"]',
    "general contractors": '["craft"="builder"]',
    "hvac": '["craft"="hvac"]',
    "plumbing": '["craft"="plumber"]',
    "electrical": '["craft"="electrician"]',
    "landscaping": '["craft"="gardener"]',
    "painting": '["craft"="painter"]',
    "solar": '["craft"="electrician"]',
    "dental": '["amenity"="dentist"]',
    "medical": '["amenity"="clinic"]',
    "law firms": '["office"="lawyer"]',
    "restaurants": '["amenity"="restaurant"]',
    "automotive": '["shop"="car_repair"]'
}

class OpenStreetMapDiscoveryAdapter(BaseDiscoveryAdapter):
    """
    OpenStreetMap & Overpass Business Discovery Adapter.
    Provides free, authorized public geospatial business discovery for all US locations
    without requiring third-party API billing keys.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="openstreetmap", api_key=api_key or "public", extra_config=extra_config)
        self.endpoint = "https://overpass-api.de/api/interpreter"

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
        radius_meters = int(min(radius_miles * 1609.34, 50000)) # capped per query
        
        # Build search keywords
        term = trade or industry or "contractor"
        term_clean = re.sub(r'[^\w\s]', '', term.lower()).strip()
        first_word = term_clean.split()[0] if term_clean else "roofing"
        
        osm_filter = INDUSTRY_OSM_TAG_MAPPING.get(first_word, f'["name"~"{first_word}",i]')

        query = f"""
        [out:json][timeout:15];
        (
          node{osm_filter}(around:{radius_meters},{center_lat},{center_lon});
          way{osm_filter}(around:{radius_meters},{center_lat},{center_lon});
          relation{osm_filter}(around:{radius_meters},{center_lat},{center_lon});
        );
        out center {limit * 2};
        """

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(self.endpoint, data={"data": query})
                if resp.status_code == 200:
                    data = resp.json()
                    elements = data.get("elements", [])

                    for el in elements:
                        tags = el.get("tags", {})
                        name = tags.get("name")
                        if not name:
                            continue

                        # Extract coords
                        lat = el.get("lat") or el.get("center", {}).get("lat")
                        lon = el.get("lon") or el.get("center", {}).get("lon")
                        
                        dist_miles = 0.0
                        if lat and lon:
                            is_inside, dist_miles = LocationService.is_within_radius(
                                center_lat, center_lon, float(lat), float(lon), radius_miles
                            )
                            if not is_inside:
                                continue

                        # Extract address components
                        street = tags.get("addr:street", "")
                        housenumber = tags.get("addr:housenumber", "")
                        addr_str = f"{housenumber} {street}".strip() if street else ""
                        el_city = tags.get("addr:city") or city
                        el_state = tags.get("addr:state") or state
                        el_zip = tags.get("addr:postcode", "")

                        phone = tags.get("phone") or tags.get("contact:phone") or ""
                        website = tags.get("website") or tags.get("contact:website") or ""

                        leads.append(DiscoveredLead(
                            name=name,
                            industry=industry,
                            trade=trade or industry,
                            address=addr_str or f"{el_city}, {el_state}",
                            city=el_city,
                            state=el_state,
                            zip_code=el_zip,
                            country="USA",
                            phone=phone,
                            website=website,
                            latitude=float(lat) if lat else None,
                            longitude=float(lon) if lon else None,
                            distance_miles=dist_miles,
                            provider="OpenStreetMap",
                            provider_place_id=f"osm_{el.get('type')}_{el.get('id')}",
                            raw_metadata=tags
                        ))

                        if len(leads) >= limit:
                            break
        except Exception:
            pass

        return leads
