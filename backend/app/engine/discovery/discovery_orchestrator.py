import json
from typing import Any, Optional, Callable
from sqlalchemy.orm import Session
from .base import DiscoveredLead, BaseDiscoveryAdapter
from .deduplicator import LeadDeduplicator
from .osm_discovery import OpenStreetMapDiscoveryAdapter
from .google_places_discovery import GooglePlacesDiscoveryAdapter
from .search_engine_discovery import SearchEngineDiscoveryAdapter
from ...models import ApiConfig

class BusinessDiscoveryEngine:
    """
    Master Business Discovery Engine.
    Executes modular business discovery across all enabled providers, performs deduplication,
    enforces radius filtering, and returns qualified B2B leads.
    """
    def __init__(self, session: Optional[Session] = None):
        self.adapters: list[BaseDiscoveryAdapter] = []
        self.deduplicator = LeadDeduplicator()

        # Always include high-accuracy public OpenStreetMap & Search Engine adapters
        self.osm_adapter = OpenStreetMapDiscoveryAdapter()
        self.search_adapter = SearchEngineDiscoveryAdapter()
        self.google_adapter = GooglePlacesDiscoveryAdapter()

        self.adapters.append(self.osm_adapter)
        self.adapters.append(self.search_adapter)

        if session:
            self._load_api_configs(session)

    def _load_api_configs(self, session: Session):
        """Loads user-configured API credentials from database."""
        configs = session.query(ApiConfig).filter(ApiConfig.is_enabled == True).all()
        for cfg in configs:
            if not cfg.api_key:
                continue
            p_name = cfg.provider_name.lower()
            if p_name == "google_places":
                self.google_adapter = GooglePlacesDiscoveryAdapter(api_key=cfg.api_key)
                if self.google_adapter not in self.adapters:
                    self.adapters.insert(0, self.google_adapter) # Prioritize Google Places if key exists

    def discover_leads(
        self,
        industries: list[str],
        locations: list[dict[str, Any]], # [{"city": "Houston", "state": "TX", "lat": 29.76, "lon": -95.36}]
        radius_miles: float,
        target_count: int = 100,
        on_progress: Optional[Callable[[dict[str, Any]], None]] = None
    ) -> list[DiscoveredLead]:
        """
        Executes automated discovery across multiple industries and locations.
        """
        discovered_leads: list[DiscoveredLead] = []
        duplicate_count = 0

        for loc in locations:
            city = loc.get("city") or loc.get("city_name") or ""
            state = loc.get("state") or loc.get("state_abbr") or "TX"
            lat = float(loc.get("lat") or loc.get("latitude") or 0.0)
            lon = float(loc.get("lon") or loc.get("longitude") or 0.0)

            for ind in industries:
                if len(discovered_leads) >= target_count:
                    break

                for adapter in self.adapters:
                    if len(discovered_leads) >= target_count:
                        break

                    if on_progress:
                        on_progress({
                            "current_state": state,
                            "current_city": city,
                            "current_industry": ind,
                            "current_provider": adapter.name,
                            "current_stage": f"Discovering {ind} in {city}, {state} via {adapter.name}",
                            "total_discovered": len(discovered_leads) + duplicate_count,
                            "unique_discovered": len(discovered_leads),
                            "duplicate_count": duplicate_count
                        })

                    candidates = adapter.discover_sync(
                        industry=ind,
                        trade=ind,
                        city=city,
                        state=state,
                        center_lat=lat,
                        center_lon=lon,
                        radius_miles=radius_miles,
                        limit=min(target_count - len(discovered_leads), 30)
                    )

                    for cand in candidates:
                        is_dup, reason = self.deduplicator.is_duplicate(cand)
                        if is_dup:
                            duplicate_count += 1
                            continue

                        self.deduplicator.register(cand)
                        discovered_leads.append(cand)

                        if on_progress:
                            on_progress({
                                "total_discovered": len(discovered_leads) + duplicate_count,
                                "unique_discovered": len(discovered_leads),
                                "duplicate_count": duplicate_count
                            })

                        if len(discovered_leads) >= target_count:
                            break

        return discovered_leads
