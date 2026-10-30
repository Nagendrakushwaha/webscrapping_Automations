from typing import Optional, Any
import httpx
from .base import BaseAdapter, SearchResultItem

class HunterAdapter(BaseAdapter):
    """
    Hunter.io API Adapter for authentic company domain search and email verification.
    """
    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="hunter", api_key=api_key, extra_config=extra_config)
        self.endpoint_domain = "https://api.hunter.io/v2/domain-search"
        self.endpoint_verify = "https://api.hunter.io/v2/email-verifier"

    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Hunter.io API key is not configured."
        try:
            params = {"api_key": self.api_key}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get("https://api.hunter.io/v2/account", params=params)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    email = data.get("email", "")
                    return True, f"Hunter.io connection successful ({email})!"
                return False, f"Hunter.io API error: HTTP {resp.status_code} - {resp.text}"
        except Exception as e:
            return False, f"Hunter connection failed: {str(e)}"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        return []

    async def domain_search(self, domain: str) -> dict[str, Any]:
        """
        Retrieves verified emails and decision-maker contact details for a company domain.
        """
        if not self.is_configured or not domain:
            return {}
        try:
            params = {"domain": domain, "api_key": self.api_key, "limit": 10}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint_domain, params=params)
                if resp.status_code == 200:
                    return resp.json().get("data", {})
        except Exception:
            pass
        return {}

    async def verify_email(self, email: str) -> dict[str, Any]:
        """
        Performs real-time email deliverability and catch-all verification.
        """
        if not self.is_configured or not email:
            return {}
        try:
            params = {"email": email, "api_key": self.api_key}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint_verify, params=params)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {
                        "status": data.get("status", "unknown"), # valid, invalid, accept_all, unknown
                        "score": data.get("score", 0),
                        "result": data.get("result", "")
                    }
        except Exception:
            pass
        return {}

