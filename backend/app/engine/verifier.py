import re
import dns.resolver
from datetime import datetime
from typing import Any

EMAIL_SYNTAX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class DataVerifier:
    """
    Verification and Confidence Scoring System.
    Evaluates evidence quality, resolves email MX records, detects conflicts, and computes overall confidence.
    """

    @staticmethod
    def verify_email_syntax_and_mx(email: str) -> tuple[str, str]:
        """
        Validates email syntax and resolves domain MX records using DNS.
        Returns (status, reason).
        status: 'Valid', 'Invalid', 'Catch-All', 'Unknown', 'Not Found'
        """
        if not email:
            return "Not Found", "No email provided."

        clean_email = email.strip().lower()
        if not EMAIL_SYNTAX.match(clean_email):
            return "Invalid", "Failed RFC syntax validation."

        domain = clean_email.split("@")[1]
        
        # Check domain MX records
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3.0
            resolver.lifetime = 3.0
            answers = resolver.resolve(domain, 'MX')
            if answers and len(answers) > 0:
                mx_hosts = [str(r.exchange) for r in answers]
                return "Valid", f"Domain has active mail exchange servers: {', '.join(mx_hosts[:2])}"
            else:
                return "Invalid", f"Domain {domain} has no MX records."
        except dns.resolver.NXDOMAIN:
            return "Invalid", f"Domain {domain} does not exist (NXDOMAIN)."
        except dns.resolver.NoAnswer:
            return "Invalid", f"No MX records returned for {domain}."
        except Exception as e:
            # DNS lookup timed out or network isolated
            return "Unknown", f"DNS MX check inconclusive: {str(e)}"

    @staticmethod
    def calculate_confidence(
        sources_count: int, 
        has_direct_website_proof: bool, 
        identity_match_score: float, 
        is_third_party_verified: bool = False
    ) -> int:
        """
        Calculates confidence score (0 to 100) based on source consensus and evidence strength.
        90-100: Multiple independent consistent sources.
        75-89: Good evidence from reliable source.
        50-74: Partial match; review recommended.
        0-49: Weak evidence; marked unverified.
        """
        base_score = 40
        if has_direct_website_proof:
            base_score += 35
        if sources_count >= 2:
            base_score += 15
        if is_third_party_verified:
            base_score += 10
        
        # Scale by identity match score
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
        """
        Checks if two discovered values for a single-valued field conflict.
        """
        if not existing_value or not new_value:
            return False
        
        v1 = existing_value.strip().lower()
        v2 = new_value.strip().lower()
        if v1 == v2:
            return False

        # For phone numbers: compare digits
        if "phone" in field_name.lower():
            d1 = re.sub(r'\D', '', v1)
            d2 = re.sub(r'\D', '', v2)
            if d1 and d2 and d1 == d2:
                return False
            return True

        # For emails
        if "email" in field_name.lower():
            return v1 != v2

        # For names (Owner, CEO, Founder)
        if any(role in field_name.lower() for role in ["owner", "ceo", "founder"]):
            # Check if one is a substring or initials
            words1 = set(v1.split())
            words2 = set(v2.split())
            if words1 == words2 or (len(words1.intersection(words2)) >= 2):
                return False
            return True

        return False
