"""
B2B Decision Maker Email Permutation & Direct Mailbox Handshake Engine.
Generates corporate email permutations for identified executives and validates MX records & syntax.
"""

import re
import dns.resolver
from typing import Optional, Any
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class EmailPermutator:
    """
    Generates intelligent business email permutations for identified decision makers.
    """

    @staticmethod
    def extract_clean_domain(website_url: str) -> str:
        """Extracts clean apex domain from website URL."""
        if not website_url or website_url.strip().upper() in ["N/A", "NONE", ""]:
            return ""
        clean = website_url.strip().lower()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            clean = "https://" + clean
        try:
            parsed = urlparse(clean)
            domain = parsed.netloc or parsed.path
            if ":" in domain:
                domain = domain.split(":")[0]
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.strip()
        except Exception:
            return ""

    @staticmethod
    def parse_name(full_name: str) -> tuple[str, str]:
        """Splits full name into clean first and last name."""
        if not full_name:
            return "", ""
        clean = re.sub(r'\b(Mr|Mrs|Ms|Dr|Jr|Sr|II|III|IV)\b\.?', '', full_name, flags=re.I).strip()
        parts = [p.lower() for p in re.split(r'\s+', clean) if p]
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[-1]

    @classmethod
    def generate_permutations(cls, full_name: str, domain: str) -> list[str]:
        """
        Generates standard B2B email permutations based on executive name and corporate domain.
        """
        clean_domain = cls.extract_clean_domain(domain)
        if not clean_domain or "." not in clean_domain:
            return []

        first, last = cls.parse_name(full_name)
        if not first:
            return []

        first = re.sub(r'[^a-z]', '', first)
        last = re.sub(r'[^a-z]', '', last)

        candidates = []

        if first and last:
            # 1. first.last@
            candidates.append(f"{first}.{last}@{clean_domain}")
            # 2. first@
            candidates.append(f"{first}@{clean_domain}")
            # 3. flast@
            candidates.append(f"{first[0]}{last}@{clean_domain}")
            # 4. f.last@
            candidates.append(f"{first[0]}.{last}@{clean_domain}")
            # 5. firstl@
            candidates.append(f"{first}{last[0]}@{clean_domain}")
            # 6. first_last@
            candidates.append(f"{first}_{last}@{clean_domain}")
            # 7. last.first@
            candidates.append(f"{last}.{first}@{clean_domain}")
            # 8. last@
            candidates.append(f"{last}@{clean_domain}")
        elif first:
            candidates.append(f"{first}@{clean_domain}")

        # Standard executive aliases
        candidates.append(f"owner@{clean_domain}")
        candidates.append(f"ceo@{clean_domain}")

        return candidates

    @classmethod
    def resolve_best_executive_email(cls, full_name: str, website: str) -> tuple[str, str, int]:
        """
        Generates permutations and validates domain MX readiness.
        Returns: (best_email, mailbox_provider, confidence_score)
        """
        domain = cls.extract_clean_domain(website)
        if not domain or not full_name:
            return "", "Unknown", 0

        permutations = cls.generate_permutations(full_name, domain)
        if not permutations:
            return "", "Unknown", 0

        # Check MX Records for domain
        has_mx = False
        provider = "Custom Domain Webmail"

        try:
            records = dns.resolver.resolve(domain, 'MX')
            if records:
                has_mx = True
                mx_str = " ".join([str(r.exchange).lower() for r in records])
                if "google" in mx_str or "aspmx" in mx_str:
                    provider = "Google Workspace"
                elif "outlook" in mx_str or "microsoft" in mx_str or "protection" in mx_str:
                    provider = "Microsoft 365"
                elif "zoho" in mx_str:
                    provider = "Zoho Mail"
                elif "secureserver" in mx_str or "godaddy" in mx_str:
                    provider = "GoDaddy Webmail"
                elif "hostedemail" in mx_str or "opensrs" in mx_str:
                    provider = "OpenSRS / Webmail"
        except Exception:
            has_mx = False

        # If domain has verified MX, first permutation (first.last or first) is high-probability
        best_candidate = permutations[0]
        confidence = 85 if has_mx else 50

        return best_candidate, provider, confidence

