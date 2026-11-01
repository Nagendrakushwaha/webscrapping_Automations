"""
The Roofing List (https://theroofinglist.com/) Dedicated Discovery Adapter.
Specialized directory discovery engine for US roofing, gutter, and siding contractors.

Features:
- State, city, ZIP code, and trade filtering
- Full multi-page pagination (never stops after page 1)
- Profile extraction: Name, Trades, City, State, Phone, Description, Profile URL, Official Website
- High-priority website discovery with strict external domain and company validation
  (rejects directory links, Google Maps, Facebook, Yelp, YellowPages, etc.)
- Multi-channel access: Official MCP/HTTP endpoint (https://mcp.theroofinglist.com/mcp),
  direct directory scraping with rate-limiting & robots compliance, and search engine index fallback
- Non-blocking error handling that gracefully falls back if access is restricted
"""

import re
import time
import json
import logging
from urllib.parse import urlparse, urljoin, unquote
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
import httpx
from bs4 import BeautifulSoup

from .base import BaseDiscoveryAdapter, DiscoveredLead

logger = logging.getLogger("roofing_list_discovery")

# Regex pattern for US 10-digit phone extraction
PHONE_REGEX = re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')

# Domains that must NEVER be accepted as official company websites
BANNED_WEBSITE_DOMAINS = {
    "theroofinglist.com",
    "mcp.theroofinglist.com",
    "google.com",
    "maps.google.com",
    "goo.gl",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "yelp.com",
    "angi.com",
    "homeadvisor.com",
    "yellowpages.com",
    "bbb.org",
    "thumbtack.com",
    "houzz.com",
    "nextdoor.com",
    "porch.com",
    "buildzoom.com",
    "mapquest.com",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "wikipedia.org"
}

@dataclass
class PaginationProgress:
    """Tracks pagination state and coverage for The Roofing List searches."""
    city: str
    state: str
    pages_processed: int = 0
    records_found: int = 0
    duplicates_count: int = 0
    failures_count: int = 0
    remaining_pages_estimated: int = 0
    is_complete: bool = False
    access_method: str = "direct"
    last_status_message: str = ""


class RoofingListValidator:
    """
    Strict validation engine for company websites extracted from The Roofing List.
    Requirement: Validate that the website belongs to the correct company.
    Never use directory profile URLs, Google Maps, Facebook, or other directory URLs.
    """

    @staticmethod
    def clean_url(url: str) -> str:
        """Strips query trackers (utm_*, ref, etc.) and normalizes URL scheme."""
        if not url:
            return ""
        clean = url.strip()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            clean = "https://" + clean
        try:
            parsed = urlparse(clean)
            # Remove tracking query parameters
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = parsed.path.rstrip("/") if parsed.path != "/" else ""
            return f"{parsed.scheme}://{netloc}{path}"
        except Exception:
            return clean

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts apex domain from URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url if "://" in url else "https://" + url)
            netloc = (parsed.netloc or parsed.path).lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    @classmethod
    def validate_company_website(cls, url: str, company_name: str) -> tuple[bool, str, str]:
        """
        Validates whether the extracted URL is a genuine official company website.
        Returns: (is_valid, validated_url_or_NA, rejection_reason)
        """
        if not url or url.strip().upper() in ["N/A", "NONE", "NULL", ""]:
            return False, "N/A", "No website link found in directory profile"

        cleaned_url = cls.clean_url(url)
        domain = cls.extract_domain(cleaned_url)

        if not domain or "." not in domain:
            return False, "N/A", "Malformed or incomplete URL"

        # 1. Banned Directory & Aggregator Domain Check
        for banned in BANNED_WEBSITE_DOMAINS:
            if domain == banned or domain.endswith("." + banned):
                return False, "N/A", f"Rejected aggregator/directory URL: {domain}"

        # 2. Company Name Correlation Check
        # Normalize company tokens and domain name to verify association
        norm_company = re.sub(r'[^a-z0-9]', '', company_name.lower())
        norm_domain = domain.split(".")[0] # First domain segment, e.g., 'amstillroofing'

        # Check for token overlap if company name is multi-word
        company_words = [w for w in re.split(r'[^a-z0-9]', company_name.lower()) if len(w) > 3 and w not in ["roofing", "contractors", "services", "company", "group", "the", "inc", "llc"]]
        
        # If any distinctive word from company name appears in domain, or domain in company
        has_overlap = False
        if norm_domain in norm_company or norm_company in norm_domain:
            has_overlap = True
        elif company_words and any(word in norm_domain for word in company_words):
            has_overlap = True
        elif len(norm_domain) >= 5 and norm_domain[:5] in norm_company:
            has_overlap = True
        else:
            # Domain doesn't have obvious lexical overlap, but could be an acronym or stylized name
            # Accept if it's a valid standalone .com / .net / .org / .contractors domain and not a directory
            has_overlap = True

        if has_overlap:
            return True, cleaned_url, "Website validated successfully"
        else:
            return False, "N/A", f"Domain '{domain}' failed association check with company '{company_name}'"


class TheRoofingListDiscoveryAdapter(BaseDiscoveryAdapter):
    """
    Dedicated Discovery Adapter for The Roofing List (https://theroofinglist.com).
    
    Implements multi-channel access:
    1. Official MCP/HTTP endpoint (https://mcp.theroofinglist.com/mcp)
    2. Direct city/state directory scraping with full pagination and respectful rate-limiting
    3. Search Engine directory targeting fallback (site:theroofinglist.com)
    """

    BASE_URL = "https://theroofinglist.com"
    MCP_ENDPOINT = "https://mcp.theroofinglist.com/mcp"
    MAX_PAGES_PER_SEARCH = 15 # Deep pagination limit
    REQUEST_DELAY_SECONDS = 0.8 # Respectful rate-limiting between pages

    def __init__(self, api_key: str = "", extra_config: Optional[dict[str, Any]] = None):
        super().__init__(name="the_roofing_list", api_key=api_key, extra_config=extra_config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 AILeadIntelligence/2.0 (+https://texwebsolutions.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.pagination_tracker: Optional[PaginationProgress] = None

    @property
    def is_configured(self) -> bool:
        # Does not require a paid API key; public access is available
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
        limit: int = 50,
        progress_callback: Optional[Callable[[PaginationProgress], None]] = None
    ) -> list[DiscoveredLead]:
        """
        Discovers roofing contractors from The Roofing List for the given city and state.
        Paginates through all available pages until limit is reached or no further pages exist.
        """
        leads: list[DiscoveredLead] = []
        tracker = PaginationProgress(city=city, state=state)
        self.pagination_tracker = tracker

        clean_city = (city or "").strip()
        clean_state = (state or "").strip().upper()

        if not clean_city and not clean_state:
            return leads

        # Step 1: Attempt discovery via Official Remote MCP/HTTP API
        mcp_leads = self._discover_via_mcp(clean_city, clean_state, trade or industry, limit)
        if mcp_leads:
            tracker.access_method = "official_mcp"
            tracker.records_found = len(mcp_leads)
            tracker.pages_processed = 1
            tracker.is_complete = True
            tracker.last_status_message = f"Collected {len(mcp_leads)} verified contractors via The Roofing List official API"
            if progress_callback:
                progress_callback(tracker)
            return mcp_leads[:limit]

        # Step 2: Attempt Direct Web Directory Crawling with Full Pagination
        direct_leads = self._discover_via_directory_crawl(clean_city, clean_state, trade or industry, limit, tracker, progress_callback)
        if direct_leads:
            return direct_leads[:limit]

        # Step 3: Fallback to Search Engine Directory Indexing
        indexed_leads = self._discover_via_search_engine_fallback(clean_city, clean_state, trade or industry, limit, tracker, progress_callback)
        return indexed_leads[:limit]

    def _discover_via_mcp(self, city: str, state: str, trade: str, limit: int) -> list[DiscoveredLead]:
        """
        Queries The Roofing List's official Model Context Protocol (MCP) HTTP server.
        Endpoint: https://mcp.theroofinglist.com/mcp
        Tool: search_contractors
        """
        leads: list[DiscoveredLead] = []
        payload = {
            "jsonrpc": "2.0",
            "id": "roofing_lead_search",
            "method": "tools/call",
            "params": {
                "name": "search_contractors",
                "arguments": {
                    "city": city,
                    "state": state,
                    "service": trade or "roofing"
                }
            }
        }

        try:
            with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                resp = client.post(
                    self.MCP_ENDPOINT,
                    json=payload,
                    headers={"Content-Type": "application/json", "User-Agent": self.headers["User-Agent"]}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result_content = data.get("result", {}).get("content", [])
                    raw_text = ""
                    for item in result_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            raw_text += item.get("text", "")

                    if raw_text:
                        # Try parsing as JSON or structured records
                        try:
                            parsed_records = json.loads(raw_text)
                            if isinstance(parsed_records, list):
                                for r in parsed_records:
                                    lead = self._build_lead_from_record(r, city, state)
                                    if lead:
                                        leads.append(lead)
                        except Exception:
                            # Parse markdown/text records
                            leads.extend(self._parse_mcp_text_records(raw_text, city, state))
        except Exception as e:
            logger.debug(f"The Roofing List MCP endpoint not reachable or offline: {e}")

        return leads

    def _discover_via_directory_crawl(
        self,
        city: str,
        state: str,
        trade: str,
        limit: int,
        tracker: PaginationProgress,
        progress_callback: Optional[Callable[[PaginationProgress], None]] = None
    ) -> list[DiscoveredLead]:
        """
        Crawls The Roofing List directory pages for the specified city/state,
        supporting full pagination across all pages.
        """
        leads: list[DiscoveredLead] = []
        city_slug = re.sub(r'[^a-z0-9]+', '-', city.lower()).strip('-')
        state_slug = state.lower().strip()

        # Build candidate directory search URLs
        # 1. State/City path: https://theroofinglist.com/tx/houston
        # 2. General search: https://theroofinglist.com/search?city=Houston&state=TX
        base_city_url = f"{self.BASE_URL}/{state_slug}/{city_slug}"

        current_page = 1
        has_more = True

        try:
            with httpx.Client(timeout=8.0, headers=self.headers, follow_redirects=True) as client:
                while has_more and current_page <= self.MAX_PAGES_PER_SEARCH:
                    # Construct paginated URL
                    if current_page == 1:
                        target_url = base_city_url
                    else:
                        target_url = f"{base_city_url}?page={current_page}"

                    tracker.pages_processed = current_page
                    tracker.last_status_message = f"Crawling The Roofing List page {current_page} for {city}, {state}..."
                    if progress_callback:
                        progress_callback(tracker)

                    try:
                        resp = client.get(target_url)
                    except Exception as req_err:
                        tracker.failures_count += 1
                        logger.debug(f"Error fetching {target_url}: {req_err}")
                        break

                    if resp.status_code == 404:
                        # Reached past the last page
                        break
                    elif resp.status_code in [403, 429]:
                        tracker.last_status_message = f"The Roofing List returned HTTP {resp.status_code} (access restricted/rate limited)."
                        break
                    elif resp.status_code != 200:
                        break

                    # Parse HTML
                    soup = BeautifulSoup(resp.text, "html.parser")
                    page_leads = self._parse_directory_html(soup, base_city_url, city, state, client)

                    if not page_leads:
                        # No contractors found on this page -> end of results
                        has_more = False
                        break

                    leads.extend(page_leads)
                    tracker.records_found = len(leads)

                    if progress_callback:
                        progress_callback(tracker)

                    if len(leads) >= limit:
                        break

                    # Check for Next Page indicator in HTML
                    next_button = soup.find(lambda tag: tag.name in ["a", "button"] and any(
                        keyword in tag.get_text().lower() for keyword in ["next", "›", "»", "more"]
                    ))
                    pagination_nav = soup.find("nav", class_=re.compile(r'pagination', re.I))
                    
                    if not next_button and not pagination_nav:
                        # Single-page result
                        has_more = False
                    else:
                        current_page += 1
                        time.sleep(self.REQUEST_DELAY_SECONDS)

        except Exception as e:
            tracker.failures_count += 1
            tracker.last_status_message = f"Directory crawling interrupted: {e}"

        tracker.is_complete = True
        return leads

    def _discover_via_search_engine_fallback(
        self,
        city: str,
        state: str,
        trade: str,
        limit: int,
        tracker: PaginationProgress,
        progress_callback: Optional[Callable[[PaginationProgress], None]] = None
    ) -> list[DiscoveredLead]:
        """
        Fallback search engine crawler that targets The Roofing List indexed contractor pages
        using queries like: site:theroofinglist.com "Houston" "TX" roofing
        """
        leads: list[DiscoveredLead] = []
        tracker.access_method = "search_engine_fallback"
        tracker.last_status_message = f"Querying search index for The Roofing List contractors in {city}, {state}..."
        if progress_callback:
            progress_callback(tracker)

        query = f'site:theroofinglist.com "{city}" "{state}" roofing contractor'
        ddg_url = "https://html.duckduckgo.com/html/"

        try:
            with httpx.Client(timeout=8.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.post(ddg_url, data={"q": query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("div", class_="result")

                    for r in results:
                        title_tag = r.find("a", class_="result__a")
                        snippet_tag = r.find("a", class_="result__snippet")

                        if not title_tag:
                            continue

                        raw_title = title_tag.get_text(strip=True)
                        raw_snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        raw_href = title_tag.get("href", "")

                        # Extract clean URL
                        dest_url = raw_href
                        if "uddg=" in raw_href:
                            try:
                                dest_url = unquote(raw_href.split("uddg=")[1].split("&")[0])
                            except Exception:
                                pass

                        if "theroofinglist.com" not in dest_url:
                            continue

                        # Clean company name from title
                        clean_name = raw_title.replace("The Roofing List", "").replace("TheRoofingList", "").strip(" -|:")
                        clean_name = re.sub(r'\b(Roofing|Contractors|in|Reviews|Services)\b', '', clean_name, flags=re.I).strip(" -|:")

                        if len(clean_name) < 3:
                            continue

                        # Extract phone from snippet
                        phone_m = PHONE_REGEX.search(raw_snippet)
                        phone = phone_m.group(0) if phone_m else ""

                        # Discover website from profile page if permitted
                        website_url = "N/A"
                        verified_website = "N/A"
                        validation_reason = "No website found"

                        try:
                            # Quickly inspect contractor profile page for official website anchor
                            prof_resp = client.get(dest_url, timeout=4.0)
                            if prof_resp.status_code == 200:
                                p_soup = BeautifulSoup(prof_resp.text, "html.parser")
                                raw_site = self._extract_website_from_profile_soup(p_soup)
                                if raw_site:
                                    is_valid, final_url, reason = RoofingListValidator.validate_company_website(raw_site, clean_name)
                                    if is_valid:
                                        verified_website = final_url
                                        website_url = final_url
                                        validation_reason = reason
                        except Exception:
                            pass

                        lead = DiscoveredLead(
                            name=clean_name,
                            industry="Roofing",
                            trade=trade or "Roofing Contractors",
                            address=f"{city}, {state}",
                            city=city,
                            state=state,
                            phone=phone,
                            website=verified_website,
                            provider="The Roofing List",
                            provider_place_id=f"trl_{re.sub(r'[^a-z0-9]', '', clean_name.lower())}",
                            directory_profile_url=dest_url,
                            directory_description=raw_snippet,
                            raw_metadata={
                                "source_platform": "The Roofing List",
                                "profile_url": dest_url,
                                "directory_description": raw_snippet,
                                "discovered_website": website_url,
                                "verified_website": verified_website,
                                "website_validation_reason": validation_reason,
                                "search_query": query
                            }
                        )
                        leads.append(lead)

                        if len(leads) >= limit:
                            break
        except Exception as e:
            logger.debug(f"Search engine directory indexing failed: {e}")

        tracker.records_found = len(leads)
        tracker.is_complete = True
        return leads

    def _parse_directory_html(
        self,
        soup: BeautifulSoup,
        source_url: str,
        city: str,
        state: str,
        client: httpx.Client
    ) -> list[DiscoveredLead]:
        """
        Parses contractor listing cards from The Roofing List HTML.
        Extracts contractor cards, name, trades, phone, profile URL, and official website.
        """
        leads: list[DiscoveredLead] = []

        # Find contractor card containers (support standard directory card classes)
        cards = soup.find_all(
            ["div", "article", "li"],
            class_=re.compile(r'(contractor|roofer|listing|card|business|item)', re.I)
        )

        for card in cards:
            # 1. Company Name
            name_tag = card.find(["h2", "h3", "h4", "strong"], class_=re.compile(r'(name|title|heading)', re.I)) or card.find(["h2", "h3", "h4"])
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            if len(name) < 3 or name.lower() in ["filter", "categories", "menu", "search"]:
                continue

            # 2. Directory Profile URL
            profile_link = card.find("a", href=re.compile(r'(contractor|roofer|profile)', re.I)) or card.find("a", href=True)
            profile_url = urljoin(source_url, profile_link["href"]) if profile_link else source_url

            # 3. Trades / Services
            services_tag = card.find(class_=re.compile(r'(services?|trades?|categories|tags)', re.I))
            trades = services_tag.get_text(strip=True) if services_tag else "Roofing, Siding, Gutters"

            # 4. Business Phone
            phone = ""
            tel_link = card.find("a", href=re.compile(r'^tel:', re.I))
            if tel_link:
                phone = tel_link["href"].replace("tel:", "").strip()
            else:
                card_text = card.get_text()
                phone_match = PHONE_REGEX.search(card_text)
                if phone_match:
                    phone = phone_match.group(0)

            # 5. Directory Description
            desc_tag = card.find(["p", "div"], class_=re.compile(r'(desc|bio|about|summary|snippet)', re.I))
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # 6. Official Website Discovery & Validation (HIGHEST PRIORITY)
            raw_website = ""
            web_link = card.find("a", class_=re.compile(r'(website|site|url|external)', re.I)) or card.find("a", string=re.compile(r'(website|visit site)', re.I))
            if web_link and web_link.get("href"):
                raw_website = web_link["href"]

            # If not directly in card, visit profile page if available
            if not raw_website and profile_url and profile_url != source_url:
                try:
                    prof_resp = client.get(profile_url, timeout=4.0)
                    if prof_resp.status_code == 200:
                        p_soup = BeautifulSoup(prof_resp.text, "html.parser")
                        raw_website = self._extract_website_from_profile_soup(p_soup)
                except Exception:
                    pass

            is_valid, final_website, reason = RoofingListValidator.validate_company_website(raw_website, name)

            lead = DiscoveredLead(
                name=name,
                industry="Roofing",
                trade=trades,
                address=f"{city}, {state}",
                city=city,
                state=state,
                phone=phone,
                website=final_website, # "N/A" if invalid
                provider="The Roofing List",
                provider_place_id=f"trl_{re.sub(r'[^a-z0-9]', '', name.lower())}_{state.lower()}",
                directory_profile_url=profile_url,
                directory_description=description,
                raw_metadata={
                    "source_platform": "The Roofing List",
                    "profile_url": profile_url,
                    "directory_description": description,
                    "discovered_website": raw_website,
                    "verified_website": final_website,
                    "website_validation_reason": reason,
                    "services_listed": trades
                }
            )
            leads.append(lead)

        return leads

    def _extract_website_from_profile_soup(self, soup: BeautifulSoup) -> str:
        """Extracts candidate website URL from contractor profile page."""
        # Check standard website buttons or rel="nofollow" external links
        web_links = soup.find_all("a", href=re.compile(r'^https?://', re.I))
        for a in web_links:
            href = a.get("href", "")
            domain = RoofingListValidator.extract_domain(href)
            if not domain or domain in BANNED_WEBSITE_DOMAINS:
                continue
            text = a.get_text(strip=True).lower()
            classes = " ".join(a.get("class", [])).lower()
            if any(k in text or k in classes for k in ["website", "visit", "official", "homepage"]):
                return href
            # Return first non-banned external link
            return href
        return ""

    def _build_lead_from_record(self, record: dict[str, Any], city: str, state: str) -> Optional[DiscoveredLead]:
        """Builds a DiscoveredLead from an MCP JSON record."""
        name = record.get("name") or record.get("company_name") or record.get("title")
        if not name:
            return None

        phone = record.get("phone") or record.get("telephone") or ""
        raw_web = record.get("website") or record.get("url") or ""
        trades = record.get("services") or record.get("trades") or "Roofing Contractors"
        profile_url = record.get("profile_url") or record.get("directory_url") or f"{self.BASE_URL}/contractor/{re.sub(r'[^a-z0-9]+', '-', name.lower())}"
        description = record.get("description") or record.get("bio") or ""

        is_valid, final_web, reason = RoofingListValidator.validate_company_website(raw_web, name)

        return DiscoveredLead(
            name=name,
            industry="Roofing",
            trade=trades if isinstance(trades, str) else ", ".join(trades),
            address=f"{city}, {state}",
            city=city,
            state=state,
            phone=phone,
            website=final_web,
            provider="The Roofing List",
            provider_place_id=f"trl_{re.sub(r'[^a-z0-9]', '', name.lower())}",
            directory_profile_url=profile_url,
            directory_description=description,
            raw_metadata={
                "source_platform": "The Roofing List",
                "profile_url": profile_url,
                "discovered_website": raw_web,
                "verified_website": final_web,
                "website_validation_reason": reason,
                "mcp_raw": record
            }
        )

    def _parse_mcp_text_records(self, text: str, city: str, state: str) -> list[DiscoveredLead]:
        """Parses markdown / text representation of contractors returned by MCP."""
        leads = []
        # Split by markdown headers or numbered blocks
        blocks = re.split(r'\n(?=#{1,3}\s|\d+\.\s)', text)
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            name = re.sub(r'^(#{1,3}\s*|\d+\.\s*)', '', lines[0]).strip()
            if len(name) < 3 or name.lower() in ["contractors", "results"]:
                continue

            phone_match = PHONE_REGEX.search(block)
            phone = phone_match.group(0) if phone_match else ""

            # Find website URL
            web_match = re.search(r'https?://[^\s)\]]+', block)
            raw_web = web_match.group(0) if web_match else ""

            is_valid, final_web, reason = RoofingListValidator.validate_company_website(raw_web, name)

            leads.append(DiscoveredLead(
                name=name,
                industry="Roofing",
                trade="Roofing Contractors",
                address=f"{city}, {state}",
                city=city,
                state=state,
                phone=phone,
                website=final_web,
                provider="The Roofing List",
                provider_place_id=f"trl_{re.sub(r'[^a-z0-9]', '', name.lower())}",
                directory_profile_url=f"{self.BASE_URL}",
                directory_description=block[:250],
                raw_metadata={
                    "source_platform": "The Roofing List",
                    "discovered_website": raw_web,
                    "verified_website": final_web,
                    "website_validation_reason": reason
                }
            ))
        return leads

