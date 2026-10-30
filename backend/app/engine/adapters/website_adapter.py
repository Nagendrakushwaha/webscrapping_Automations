import re
import json
from urllib.parse import urljoin, urlparse
from typing import Any, Optional
import httpx
from bs4 import BeautifulSoup
from .base import BaseAdapter, SearchResultItem
from ...config import settings

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')
YEAR_EST_REGEX = re.compile(r'(?:established|est\.?|founded|since)\s*[:\-]?\s*(19\d{2}|20\d{2})', re.IGNORECASE)

KEY_PAGES = [
    "", # Homepage
    "about", "about-us", "our-story", "who-we-are",
    "contact", "contact-us", "get-in-touch",
    "team", "our-team", "leadership", "staff", "meet-the-team",
    "services"
]

class WebsiteAdapter(BaseAdapter):
    """
    Direct Company Website Crawler and Extractor.
    Explores official domain pages to extract emails, phones, socials, decision makers, and schema.
    """
    def __init__(self):
        super().__init__(name="website", api_key="built_in")

    @property
    def is_configured(self) -> bool:
        return True

    async def test_connection(self) -> tuple[bool, str]:
        return True, "Direct website crawler is active and built-in."

    async def search(self, query: str, max_results: int = 5) -> list[SearchResultItem]:
        return []

    async def crawl_and_extract(self, base_url: str) -> dict[str, Any]:
        """
        Deep crawls the website's key pages and extracts comprehensive lead information.
        """
        if not base_url:
            return {"status": "No Official Website", "evidence": []}

        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "https://" + base_url

        parsed = urlparse(base_url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        result: dict[str, Any] = {
            "official_website": base_url,
            "domain": domain,
            "website_status": "Unverified",
            "title": "",
            "description": "",
            "address": "",
            "zip_code": "",
            "year_established": "",
            "emails": set(),
            "phones": set(),
            "personal_linkedin": None,
            "business_linkedin": None,
            "business_instagram": None,
            "business_facebook": None,
            "decision_makers": [],
            "pages_found": {},
            "evidence": []
        }

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

        async with httpx.AsyncClient(timeout=12.0, verify=False, follow_redirects=True, headers=headers) as client:
            # 1. First probe base URL
            try:
                resp = await client.get(base_url)
                if resp.status_code < 400:
                    result["website_status"] = "Active"
                    result["official_website"] = str(resp.url)
                elif resp.status_code in [301, 302, 307, 308]:
                    result["website_status"] = "Redirected"
                    result["official_website"] = str(resp.url)
                else:
                    result["website_status"] = f"Broken (Status {resp.status_code})"
                    return result
            except Exception as e:
                # Try with http if https fails
                if base_url.startswith("https://"):
                    try:
                        http_url = base_url.replace("https://", "http://", 1)
                        resp = await client.get(http_url)
                        if resp.status_code < 400:
                            result["website_status"] = "Active"
                            result["official_website"] = str(resp.url)
                        else:
                            result["website_status"] = "Broken"
                            return result
                    except Exception:
                        result["website_status"] = "Broken"
                        return result
                else:
                    result["website_status"] = "Broken"
                    return result

            # Parse homepage
            self._extract_from_html(resp.text, str(resp.url), result, is_home=True)

            # 2. Discover subpages
            soup = BeautifulSoup(resp.text, "html.parser")
            internal_links: dict[str, str] = {} # page_type -> url

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                abs_url = urljoin(str(resp.url), href)
                parsed_href = urlparse(abs_url)

                # Ensure it's internal
                href_domain = parsed_href.netloc.lower()
                if href_domain.startswith("www."):
                    href_domain = href_domain[4:]
                if href_domain != domain:
                    continue

                path = parsed_href.path.lower().strip("/")
                for candidate in KEY_PAGES[1:]:
                    if candidate in path and candidate not in internal_links:
                        internal_links[candidate] = abs_url

            # Crawl up to 4 key subpages (about, contact, team, services)
            for page_type, page_url in list(internal_links.items())[:4]:
                try:
                    sub_resp = await client.get(page_url)
                    if sub_resp.status_code == 200:
                        result["pages_found"][page_type] = page_url
                        self._extract_from_html(sub_resp.text, page_url, result, is_home=False)
                except Exception:
                    continue

        # Convert sets to sorted lists
        result["emails"] = sorted(list(result["emails"]))
        result["phones"] = sorted(list(result["phones"]))
        return result

    def _extract_from_html(self, html: str, current_url: str, result: dict[str, Any], is_home: bool = False):
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return

        # Title & Meta Description on Homepage
        if is_home:
            title_tag = soup.find("title")
            if title_tag and title_tag.text:
                result["title"] = title_tag.text.strip()
            
            meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()

        # Schema.org JSON-LD extraction
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                self._extract_from_json_ld(data, current_url, result)
            except Exception:
                continue

        # 1. Emails: mailto links and regex
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                clean_email = href.split(":", 1)[1].split("?")[0].strip().lower()
                if clean_email and "@" in clean_email and not clean_email.endswith((".png", ".jpg", ".svg")):
                    result["emails"].add(clean_email)
                    result["evidence"].append({
                        "field_name": "Business Email",
                        "discovered_value": clean_email,
                        "source_name": "Website Crawler",
                        "source_url": current_url,
                        "confidence_score": 95,
                        "verification_status": "Verified",
                        "notes": f"Discovered directly via mailto: link on {current_url}"
                    })

        for match in EMAIL_REGEX.finditer(html):
            em = match.group(0).lower().strip(".,;:()")
            if not em.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")) and "sentry" not in em and "example" not in em:
                result["emails"].add(em)

        # 2. Phones: tel links and regex
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("tel:"):
                raw_ph = href.split(":", 1)[1].strip()
                clean_ph = re.sub(r'[^\d+]', '', raw_ph)
                if len(clean_ph) >= 10:
                    formatted_phone = raw_ph
                    result["phones"].add(formatted_phone)
                    result["evidence"].append({
                        "field_name": "Business Phone",
                        "discovered_value": formatted_phone,
                        "source_name": "Website Crawler",
                        "source_url": current_url,
                        "confidence_score": 95,
                        "verification_status": "Verified",
                        "notes": f"Discovered directly via tel: link on {current_url}"
                    })

        # 3. Social Media Links
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            # Personal LinkedIn
            if "linkedin.com/in/" in href.lower() and not result["personal_linkedin"]:
                clean_url = href.split("?")[0].rstrip("/")
                result["personal_linkedin"] = clean_url
                result["evidence"].append({
                    "field_name": "Personal LinkedIn",
                    "discovered_value": clean_url,
                    "source_name": "Website Crawler",
                    "source_url": current_url,
                    "confidence_score": 90,
                    "verification_status": "Verified",
                    "notes": f"Personal profile link linked from company website: {current_url}"
                })
            # Business LinkedIn
            elif "linkedin.com/company/" in href.lower() and not result["business_linkedin"]:
                clean_url = href.split("?")[0].rstrip("/")
                result["business_linkedin"] = clean_url
                result["evidence"].append({
                    "field_name": "Business LinkedIn",
                    "discovered_value": clean_url,
                    "source_name": "Website Crawler",
                    "source_url": current_url,
                    "confidence_score": 95,
                    "verification_status": "Verified",
                    "notes": f"Official company LinkedIn linked on site: {current_url}"
                })
            # Business Instagram
            elif "instagram.com/" in href.lower() and not result["business_instagram"]:
                # Exclude static/share links
                if not any(x in href.lower() for x in ["/share", "/intent", "instagram.com/p/"]):
                    clean_url = href.split("?")[0].rstrip("/")
                    result["business_instagram"] = clean_url
                    result["evidence"].append({
                        "field_name": "Business Instagram",
                        "discovered_value": clean_url,
                        "source_name": "Website Crawler",
                        "source_url": current_url,
                        "confidence_score": 95,
                        "verification_status": "Verified",
                        "notes": f"Official Instagram profile linked on site: {current_url}"
                    })
            # Business Facebook
            elif "facebook.com/" in href.lower() and not result["business_facebook"]:
                if not any(x in href.lower() for x in ["/sharer", "/share.php", "/dialog/"]):
                    clean_url = href.split("?")[0].rstrip("/")
                    result["business_facebook"] = clean_url
                    result["evidence"].append({
                        "field_name": "Business Facebook",
                        "discovered_value": clean_url,
                        "source_name": "Website Crawler",
                        "source_url": current_url,
                        "confidence_score": 95,
                        "verification_status": "Verified",
                        "notes": f"Official Facebook profile linked on site: {current_url}"
                    })

        # 4. Year Established regex
        text_content = soup.get_text(separator=" ")
        est_match = YEAR_EST_REGEX.search(text_content)
        if est_match and not result["year_established"]:
            year = est_match.group(1)
            result["year_established"] = year
            result["evidence"].append({
                "field_name": "Year Established",
                "discovered_value": year,
                "source_name": "Website Crawler",
                "source_url": current_url,
                "confidence_score": 85,
                "verification_status": "Verified",
                "notes": f"Discovered in page text: '{est_match.group(0)}' on {current_url}"
            })

        # 5. Leadership & Team Detection from page structure
        self._extract_team_members(soup, current_url, result)

    def _extract_from_json_ld(self, data: Any, current_url: str, result: dict[str, Any]):
        if isinstance(data, list):
            for item in data:
                self._extract_from_json_ld(item, current_url, result)
            return

        if not isinstance(data, dict):
            return

        item_type = data.get("@type", "")
        if isinstance(item_type, list):
            item_type = " ".join(item_type)

        # Address
        if "address" in data:
            addr = data["address"]
            if isinstance(addr, dict):
                parts = [
                    addr.get("streetAddress", ""),
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("postalCode", "")
                ]
                clean_addr = ", ".join(p for p in parts if p)
                if clean_addr and not result["address"]:
                    result["address"] = clean_addr
                    result["zip_code"] = addr.get("postalCode", "")

        # Phone
        if "telephone" in data and data["telephone"]:
            ph = str(data["telephone"]).strip()
            result["phones"].add(ph)

        # Email
        if "email" in data and data["email"]:
            em = str(data["email"]).strip().lower()
            result["emails"].add(em)

        # Founder / Owner in Schema
        for role in ["founder", "alumni", "employee", "member"]:
            if role in data:
                person = data[role]
                if isinstance(person, dict) and "name" in person:
                    p_name = person.get("name", "").strip()
                    p_title = person.get("jobTitle", "Founder")
                    if p_name:
                        result["decision_makers"].append({
                            "name": p_name,
                            "title": p_title,
                            "role_type": "Founder",
                            "source_url": current_url
                        })

    def _extract_team_members(self, soup: BeautifulSoup, current_url: str, result: dict[str, Any]):
        """
        Scans for headings and cards with Owner, CEO, Founder, President titles.
        """
        ROLE_PATTERNS = [
            (re.compile(r'\b(?:owner|co-owner|business owner|proprietor)\b', re.I), "Owner"),
            (re.compile(r'\b(?:ceo|chief executive officer)\b', re.I), "CEO"),
            (re.compile(r'\b(?:founder|co-founder|cofounder)\b', re.I), "Founder"),
            (re.compile(r'\b(?:president|managing partner|principal)\b', re.I), "President"),
        ]

        # Look in cards / headers
        tags = soup.find_all(["h2", "h3", "h4", "p", "div", "span"], limit=200)
        for tag in tags:
            txt = tag.get_text(separator=" ").strip()
            if not txt or len(txt) > 120:
                continue

            for pattern, role in ROLE_PATTERNS:
                if pattern.search(txt):
                    # Check parent or siblings for name
                    parent = tag.find_parent(["div", "section", "article", "li"])
                    if parent:
                        card_text = parent.get_text(separator="\n").strip()
                        lines = [l.strip() for l in card_text.split("\n") if l.strip()]
                        # Look for a 2-3 word capitalized name
                        for line in lines:
                            if 2 <= len(line.split()) <= 4 and re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$', line):
                                if not any(w.lower() in line.lower() for w in ["roofing", "company", "services", "contact", "about", "team", "read", "more"]):
                                    result["decision_makers"].append({
                                        "name": line,
                                        "title": txt,
                                        "role_type": role,
                                        "source_url": current_url
                                    })
                                    break
