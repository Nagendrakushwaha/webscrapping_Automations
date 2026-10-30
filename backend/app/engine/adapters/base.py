from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    source_name: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    extra: dict[str, Any] = field(default_factory=dict)

class BaseAdapter(ABC):
    """
    Abstract Base Adapter for external search and data providers.
    """
    def __init__(self, name: str, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        self.name = name
        self.api_key = api_key
        self.extra_config = extra_config or {}
        self.is_enabled = True

    @property
    def is_configured(self) -> bool:
        """Returns True if the adapter has the required credentials configured."""
        return bool(self.api_key.strip())

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        """Executes a search query and returns standardized SearchResultItem records."""
        pass

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """Tests the credentials and connection against the provider."""
        pass
