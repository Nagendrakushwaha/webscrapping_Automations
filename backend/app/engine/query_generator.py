import re
from typing import Any
from urllib.parse import urlparse

class QueryGenerator:
    """
    Intelligent Search Query Generator for Multi-Source B2B Lead Research.
    Generates tailored, field-specific queries using company variations, location, and site operators.
    """

    @staticmethod
    def clean_company_name(name: str) -> tuple[str, str]:
        """
        Returns (legal_name, short_name).
        E.g. 'ABC Roofing LLC' -> ('ABC Roofing LLC', 'ABC Roofing')
        """
        clean = re.sub(r'[\(\)\[\],]', ' ', name).strip()
        clean = re.sub(r'\s+', ' ', clean)
        # Strip common legal entity suffixes for short name
        short = re.sub(
            r'\b(llc|inc|corp|corporation|ltd|limited|co|company|group|services|enterprises)\b', 
            '', 
            clean, 
            flags=re.IGNORECASE
        ).strip()
        short = re.sub(r'\s+', ' ', short)
        return clean, short if short else clean

    @staticmethod
    def extract_domain(url: str) -> str:
        if not url:
            return ""
        if not url.startswith("http"):
            url = "https://" + url
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def generate_all_queries(self, company: dict[str, Any]) -> dict[str, list[str]]:
        """
        Generates targeted queries for all 12 mandatory fields plus company identity.
        """
        raw_name = company.get("name") or company.get("original_name") or ""
        legal_name, short_name = self.clean_company_name(raw_name)
        city = company.get("city") or company.get("original_city") or ""
        state = company.get("state") or company.get("original_state") or ""
        raw_website = company.get("website url") or company.get("original_website") or ""
        domain = self.extract_domain(raw_website)
        phone = company.get("phone") or company.get("original_phone") or ""

        loc_str = f"{city} {state}".strip()

        queries: dict[str, list[str]] = {
            # Identity & General
            "identity": [
                f'"{legal_name}" {loc_str}'.strip(),
                f'"{short_name}" {loc_str}'.strip() if short_name != legal_name else "",
                f'"{legal_name}" official website',
                f'"{domain}" business address' if domain else "",
            ],

            # Field 1: Owner
            "owner": [
                f'"{legal_name}" {loc_str} owner'.strip(),
                f'"{short_name}" {loc_str} owner'.strip() if short_name != legal_name else "",
                f'"{domain}" owner' if domain else "",
                f'site:bbb.org "{legal_name}" {loc_str}'.strip(),
            ],

            # Field 2: CEO
            "ceo": [
                f'"{legal_name}" {loc_str} CEO'.strip(),
                f'"{short_name}" {loc_str} Chief Executive Officer'.strip() if short_name != legal_name else "",
                f'"{domain}" CEO' if domain else "",
            ],

            # Field 3: Founder
            "founder": [
                f'"{legal_name}" {loc_str} founder'.strip(),
                f'"{short_name}" founder'.strip() if short_name != legal_name else "",
                f'"{legal_name}" "founded by"',
            ],

            # Field 4: Co-Founder
            "cofounder": [
                f'"{legal_name}" {loc_str} "co-founder"'.strip(),
                f'"{short_name}" cofounder'.strip() if short_name != legal_name else "",
            ],

            # Field 5: Business Email
            "business_email": [
                f'"{legal_name}" contact email',
                f'"{legal_name}" sales email',
                f'"{domain}" "info@" OR "contact@" OR "sales@"' if domain else "",
                f'"{legal_name}" {loc_str} email'.strip(),
            ],

            # Field 6: Business Phone
            "business_phone": [
                f'"{legal_name}" {loc_str} phone number'.strip(),
                f'"{legal_name}" contact number',
                f'"{short_name}" {loc_str} telephone'.strip() if short_name != legal_name else "",
            ],

            # Field 7: Personal Professional Email
            "personal_email": [
                f'"{legal_name}" owner direct email',
                f'"{domain}" email owner CEO' if domain else "",
            ],

            # Field 8: Public Professional Phone
            "personal_phone": [
                f'"{legal_name}" owner direct phone',
                f'"{legal_name}" CEO direct line',
            ],

            # Field 9: Personal LinkedIn
            "personal_linkedin": [
                f'site:linkedin.com/in "{legal_name}" {loc_str}'.strip(),
                f'site:linkedin.com/in "{short_name}" {loc_str} owner'.strip() if short_name != legal_name else "",
                f'site:linkedin.com/in "{legal_name}" owner OR CEO OR Founder'.strip(),
                f'site:linkedin.com/in "{domain}"' if domain else "",
            ],

            # Field 10: Business LinkedIn
            "business_linkedin": [
                f'site:linkedin.com/company "{legal_name}"',
                f'site:linkedin.com/company "{short_name}"' if short_name != legal_name else "",
            ],

            # Field 11: Business Instagram
            "business_instagram": [
                f'site:instagram.com "{legal_name}" {loc_str}'.strip(),
                f'site:instagram.com "{short_name}" {loc_str}'.strip() if short_name != legal_name else "",
            ],

            # Field 12: Business Facebook
            "business_facebook": [
                f'site:facebook.com "{legal_name}" {loc_str}'.strip(),
                f'site:facebook.com "{short_name}" {loc_str}'.strip() if short_name != legal_name else "",
                f'site:facebook.com "{phone}"' if phone else "",
            ],
        }

        # Filter empty queries and remove duplicates
        cleaned_queries: dict[str, list[str]] = {}
        for category, q_list in queries.items():
            seen = set()
            clean_list = []
            for q in q_list:
                q_strip = q.strip()
                if q_strip and q_strip not in seen:
                    seen.add(q_strip)
                    clean_list.append(q_strip)
            cleaned_queries[category] = clean_list

        return cleaned_queries

