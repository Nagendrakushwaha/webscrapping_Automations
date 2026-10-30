from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class ApolloAdapter(BaseAdapter):
    """
    Apollo.io API Adapter for authentic B2B decision-maker and company contact enrichment.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="apollo", api_key=api_key, extra_config=extra_config)
        self.endpoint_org_search = "https://api.apollo.io/v1/organizations/search"
        self.endpoint_people_search = "https://api.apollo.io/v1/mixed_people/search"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Apollo API key is not configured."
        try:
            headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
            payload = {"api_key": self.api_key, "q_organization_name": "Tex Web Solutions", "page": 1, "per_page": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(self.endpoint_org_search, headers=headers, json=payload)
                if resp.status_code == 200:
                    return True, "Apollo API connection successful!"
                return False, f"Apollo API error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Apollo connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        if not self.is_configured:
            return []
        try:
            headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
            payload = {"api_key": self.api_key, "q_organization_name": query, "page": 1, "per_page": max_results}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.endpoint_org_search, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for org in data.get("organizations", []):
                        name = org.get("name", "")
                        domain = org.get("primary_domain", "")
                        phone = org.get("sanitized_phone", "")
                        linkedin = org.get("linkedin_url", "")
                        snippet = f"Org: {name} | Phone: {phone} | Domain: {domain}"
                        results.append(SearchResultItem(
                            title=name,
                            url=f"https://{domain}" if domain else linkedin,
                            snippet=snippet,
                            source_name="Apollo",
                            extra=org
                        ))
                    return results
        except Exception:
            return []
        return []

    async def search_decision_makers(self, domain: str, titles: list[str]) -> list[dict[str, Any]]:
        """
        Searches Apollo for senior decision-makers (Owner, CEO, Founder, President) associated with a company domain.
        """
        if not self.is_configured or not domain:
            return []
        try:
            headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
            payload = {
                "api_key": self.api_key,
                "q_organization_domains": [domain],
                "person_titles": titles or ["Owner", "CEO", "Founder", "President"],
                "page": 1,
                "per_page": 5
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.endpoint_people_search, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    people = []
                    for p in data.get("people", []):
                        people.append({
                            "name": p.get("name", ""),
                            "title": p.get("title", ""),
                            "email": p.get("email", ""),
                            "phone": p.get("phone", ""),
                            "linkedin_url": p.get("linkedin_url", ""),
                            "confidence": 95,
                            "source": "Apollo B2B"
                        })
                    return people
        except Exception:
            pass
        return []

