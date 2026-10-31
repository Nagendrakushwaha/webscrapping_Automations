import re
from urllib.parse import urlparse
from typing import Optional
from .base import DiscoveredLead

LEGAL_SUFFIXES = re.compile(
    r'\b(llc|inc|incorporated|corp|corporation|co|company|ltd|limited|services|group|holdings|enterprises)\b',
    re.IGNORECASE
)

class LeadDeduplicator:
    """
    High-fidelity B2B Lead Deduplication Engine.
    Prevents duplicate leads across multiple discovery providers, cities, and overlapping search zones.
    """

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """Standardizes business names for resilient matching."""
        if not name:
            return ""
        s = name.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = LEGAL_SUFFIXES.sub('', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @staticmethod
    def normalize_domain(url: str) -> str:
        """Extracts and normalizes the apex website domain."""
        if not url:
            return ""
        clean_url = url.strip().lower()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url
        try:
            parsed = urlparse(clean_url)
            netloc = parsed.netloc or parsed.path
            netloc = netloc.split(":")[0] # Remove port
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc.strip()
        except Exception:
            return ""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Extracts normalized 10-digit phone number."""
        if not phone:
            return ""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        return digits

    def __init__(self):
        self.seen_domains: set[str] = set()
        self.seen_phones: set[str] = set()
        self.seen_place_ids: set[str] = set()
        self.seen_name_cities: set[tuple[str, str]] = set()

    def is_duplicate(self, lead: DiscoveredLead) -> tuple[bool, str]:
        """
        Evaluates whether the lead has already been discovered.
        Returns (is_duplicate, reason).
        """
        # 1. Place ID Check (Google Places / OSM)
        if lead.provider_place_id and lead.provider_place_id in self.seen_place_ids:
            return True, f"Matched Place ID: {lead.provider_place_id}"

        # 2. Normalized Domain Check (Highest confidence duplicate signal)
        norm_domain = self.normalize_domain(lead.website)
        if norm_domain and norm_domain in self.seen_domains:
            # Skip generic platforms like facebook.com or yelp.com from deduplicating distinct businesses
            if norm_domain not in {"facebook.com", "instagram.com", "linkedin.com", "yelp.com", "yellowpages.com"}:
                return True, f"Matched Domain: {norm_domain}"

        # 3. Normalized Phone Check (High confidence signal)
        norm_phone = self.normalize_phone(lead.phone)
        if norm_phone and len(norm_phone) == 10 and norm_phone in self.seen_phones:
            return True, f"Matched Phone Number: {norm_phone}"

        # 4. Normalized Name + City Check (Protects same-name chains across different cities)
        norm_name = self.normalize_company_name(lead.name)
        norm_city = lead.city.lower().strip()
        if norm_name and norm_city:
            name_city_key = (norm_name, norm_city)
            if name_city_key in self.seen_name_cities:
                return True, f"Matched Company Name & City: {lead.name} in {lead.city}"

        return False, ""

    def register(self, lead: DiscoveredLead):
        """Registers a unique lead in the deduplication memory."""
        if lead.provider_place_id:
            self.seen_place_ids.add(lead.provider_place_id)

        norm_domain = self.normalize_domain(lead.website)
        if norm_domain and norm_domain not in {"facebook.com", "instagram.com", "linkedin.com", "yelp.com", "yellowpages.com"}:
            self.seen_domains.add(norm_domain)

        norm_phone = self.normalize_phone(lead.phone)
        if norm_phone and len(norm_phone) == 10:
            self.seen_phones.add(norm_phone)

        norm_name = self.normalize_company_name(lead.name)
        norm_city = lead.city.lower().strip()
        if norm_name and norm_city:
            self.seen_name_cities.add((norm_name, norm_city))
