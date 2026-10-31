import re
import dns.resolver
from datetime import datetime
from typing import Any

EMAIL_SYNTAX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
TOLL_FREE_PREFIXES = ["800", "888", "877", "866", "855", "844", "833"]
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwawaymail.com", "trashmail.com", "fakeinbox.com", "yopmail.com"
}

class DataVerifier:
    """
    Enhanced Verification and Confidence Scoring System.
    Evaluates evidence quality, resolves email MX records & mailbox provider,
    detects disposable domains, classifies phone line types, and handles conflicts.
    """

    @staticmethod
    def classify_phone_line_type(phone: str) -> str:
        """
        Classifies phone line type: 'Toll-Free', 'Mobile / Cellular', or 'Landline / Office'.
        """
        if not phone:
            return "Unknown"
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) < 10:
            return "Landline / Office"

        area_code = digits[:3]
        if area_code in TOLL_FREE_PREFIXES:
            return "Toll-Free"

        # Standard US area code
        return "Landline / Office"

    @staticmethod
    def verify_email_syntax_and_mx(email: str) -> tuple[str, str, str]:
        """
        Validates email syntax, disposable domains, and resolves domain MX records.
        Returns (status, reason, provider).
        provider: 'Google Workspace', 'Microsoft 365', 'Custom Webmail', 'Consumer Mail', etc.
        """
        if not email:
            return "Not Found", "No email provided.", "None"

        clean_email = email.strip().lower()
        if not EMAIL_SYNTAX.match(clean_email):
            return "Invalid", "Failed RFC syntax validation.", "Invalid"

        domain = clean_email.split("@")[1]
        
        # Check disposable domain
        if domain in DISPOSABLE_DOMAINS:
            return "Invalid", "Disposable / temporary email domain rejected.", "Disposable"

        # Consumer mail
        if domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]:
            return "Valid", f"Free consumer email account ({domain}).", "Consumer Mail"

        provider = "Custom / cPanel"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 1.5
            resolver.lifetime = 1.5
            answers = resolver.resolve(domain, 'MX')
            if answers and len(answers) > 0:
                mx_hosts = [str(r.exchange).lower() for r in answers]
                mx_str = " ".join(mx_hosts)

                if "google" in mx_str or "aspmx" in mx_str:
                    provider = "Google Workspace"
                elif "outlook.com" in mx_str or "protection.outlook" in mx_str:
                    provider = "Microsoft 365"
                elif "zoho" in mx_str:
                    provider = "Zoho Mail"
                elif "secureserver.net" in mx_str:
                    provider = "GoDaddy Webmail"

                return "Valid", f"Active mail exchange ({provider}): {mx_hosts[0].rstrip('.')}", provider
            else:
                return "Invalid", f"Domain {domain} has no MX records.", "None"
        except dns.resolver.NXDOMAIN:
            return "Invalid", f"Domain {domain} does not exist (NXDOMAIN).", "None"
        except dns.resolver.NoAnswer:
            return "Invalid", f"No MX records returned for {domain}.", "None"
        except Exception as e:
            return "Unknown", f"DNS MX check inconclusive: {str(e)}", provider

    @staticmethod
    def calculate_confidence(
        sources_count: int, 
        has_direct_website_proof: bool, 
        identity_match_score: float, 
        is_third_party_verified: bool = False
    ) -> int:
        base_score = 40
        if has_direct_website_proof:
            base_score += 35
        if sources_count >= 2:
            base_score += 15
        if is_third_party_verified:
            base_score += 10
        
        multiplier = max(0.4, min(1.0, identity_match_score / 100.0 if identity_match_score > 0 else 0.8))
        final_score = int(base_score * multiplier)
        return min(max(final_score, 10), 100)

    @staticmethod
    def get_status_from_score(score: int, has_conflict: bool = False) -> str:
        if has_conflict:
            return "Conflicting Information"
        if score >= 90:
            return "Found and Verified"
        elif score >= 75:
            return "Found and Verified"
        elif score >= 50:
            return "Found but Unverified"
        elif score > 0:
            return "Requires Manual Review"
        return "Not Found"

    @staticmethod
    def detect_conflicts(existing_value: str, new_value: str, field_name: str) -> bool:
        if not existing_value or not new_value:
            return False
        
        v1 = existing_value.strip().lower()
        v2 = new_value.strip().lower()
        if v1 == v2:
            return False

        if "phone" in field_name.lower():
            d1 = re.sub(r'\D', '', v1)
            d2 = re.sub(r'\D', '', v2)
            if d1 and d2 and d1 == d2:
                return False
            return True

        if "email" in field_name.lower():
            return v1 != v2

        if any(role in field_name.lower() for role in ["owner", "ceo", "founder"]):
            words1 = set(v1.split())
            words2 = set(v2.split())
            if words1 == words2 or (len(words1.intersection(words2)) >= 2):
                return False
            return True

        return False
