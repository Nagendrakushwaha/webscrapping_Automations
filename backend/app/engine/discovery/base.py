from dataclasses import dataclass, field
from typing import Optional, Any
from abc import ABC, abstractmethod

@dataclass
class DiscoveredLead:
    """
    Standardized Business Lead Record emitted by all discovery adapters.
    """
    name: str
    industry: str = ""
    trade: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "USA"
    phone: str = ""
    website: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_miles: float = 0.0
    provider: str = "Unknown"
    provider_place_id: str = ""
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    directory_profile_url: str = ""
    directory_description: str = ""
    raw_metadata: dict[str, Any] = field(default_factory=dict)

class BaseDiscoveryAdapter(ABC):
    """
    Abstract interface for all Business Discovery Adapters.
    """
    def __init__(self, name: str, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        self.name = name
        self.api_key = api_key
        self.extra_config = extra_config or {}

    @property
    def is_configured(self) -> bool:
        return True

    @abstractmethod
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
        """
        Discovers businesses matching criteria synchronously.
        """
        pass

