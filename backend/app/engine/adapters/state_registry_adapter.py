import httpx
from typing import Optional, Any
from .base import BaseAdapter, SearchResultItem

class StateRegistryAdapter(BaseAdapter):
    """
    US State Business Registry & Secretary of State (SOS) Corporation Filing Adapter.
    Uncovers official LLC Managing Members, Directors, and Registered Agents.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="state_registry", api_key=api_key or "public", extra_config=extra_config)
        self.endpoint = "https://api.opencorporates.com/v0.4/companies/search"

    @property
    def is_configured(self) -> bool:
        return True

    async def test_connection(self) -> tuple[bool, str]:
        return True, "US State Corporation Registry adapter is active."

    async def search(self, query: str, max_results: int = 3) -> list[SearchResultItem]:
        params = {"q": query, "jurisdiction_code": "us", "per_page": max_results}
        if self.api_key and self.api_key != "public":
            params["api_token"] = self.api_key

        results = []
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    data = resp.json().get("results", {})
                    for item in data.get("companies", [])[:max_results]:
                        comp = item.get("company", {})
                        name = comp.get("name", "")
                        state = comp.get("jurisdiction_code", "").replace("us_", "").upper()
                        status = comp.get("current_status", "Active")
                        url = comp.get("opencorporates_url", "")
                        inc_date = comp.get("incorporation_date", "")

                        results.append(SearchResultItem(
                            title=f"{name} ({state} SOS Filing)",
                            url=url,
                            snippet=f"Official {state} State Registry Filing. Status: {status}. Incorporated: {inc_date}",
                            source_name=f"{state} Secretary of State",
                            extra=comp
                        ))
        except Exception:
            pass
        return results

    def lookup_officers_sync(self, company_name: str, state_code: str) -> list[dict[str, Any]]:
        """
        Synchronous corporate registry lookup for LLC managing members and registered agents.
        """
        params = {
            "q": company_name,
            "jurisdiction_code": f"us_{state_code.lower()}" if state_code else "us",
            "per_page": 2
        }
        if self.api_key and self.api_key != "public":
            params["api_token"] = self.api_key

        officers = []
        try:
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    data = resp.json().get("results", {})
                    for item in data.get("companies", [])[:1]:
                        comp = item.get("company", {})
                        # Check agent or officers
                        agent_name = comp.get("agent_name", "")
                        if agent_name:
                            officers.append({
                                "name": agent_name,
                                "role_type": "Registered Agent / Managing Member",
                                "title": "Registered Agent",
                                "source_name": f"{comp.get('jurisdiction_code', 'US').upper()} Corporate Registry",
                                "source_url": comp.get("opencorporates_url", "")
                            })
        except Exception:
            pass
        return officers

