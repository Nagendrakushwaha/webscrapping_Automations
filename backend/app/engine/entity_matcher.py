import re
from difflib import SequenceMatcher
from urllib.parse import urlparse
from typing import Any

class EntityMatcher:
    """
    AI Entity Matching and Deduplication Engine.
    Validates company identity, decision-maker association, and social profile linkage.
    """

    @staticmethod
    def string_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        digits = re.sub(r'\D', '', phone)
        # Strip leading US country code 1 if 11 digits
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        return digits

    @staticmethod
    def extract_domain(url: str) -> str:
        if not url:
            return ""
        if not url.startswith("http"):
            url = "https://" + url
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def match_company(self, target_company: dict[str, Any], candidate_info: dict[str, Any]) -> tuple[bool, float, str]:
        """
        Determines whether candidate info belongs to the target company.
        Returns (is_match, match_confidence, reason).
        """
        score = 0.0
        reasons = []

        # 1. Domain match (strongest signal)
        target_domain = self.extract_domain(target_company.get("original_website") or target_company.get("official_website") or "")
        cand_domain = self.extract_domain(candidate_info.get("url") or candidate_info.get("website") or "")
        
        if target_domain and cand_domain and target_domain == cand_domain:
            score += 0.50
            reasons.append("Exact website domain match")

        # 2. Phone match
        target_phone = self.normalize_phone(target_company.get("original_phone") or "")
        cand_phone = self.normalize_phone(candidate_info.get("phone") or "")
        if target_phone and cand_phone and target_phone == cand_phone:
            score += 0.35
            reasons.append("Exact phone number match")

        # 3. Name similarity
        target_name = target_company.get("original_name") or ""
        cand_name = candidate_info.get("name") or candidate_info.get("title") or ""
        name_sim = self.string_similarity(target_name, cand_name)
        if name_sim >= 0.85:
            score += 0.30
            reasons.append(f"High name similarity ({int(name_sim*100)}%)")
        elif name_sim >= 0.65:
            score += 0.15
            reasons.append(f"Moderate name similarity ({int(name_sim*100)}%)")

        # 4. Location match (City / State)
        target_city = (target_company.get("original_city") or "").lower().strip()
        target_state = (target_company.get("original_state") or "").lower().strip()
        cand_text = f"{candidate_info.get('snippet', '')} {candidate_info.get('address', '')}".lower()
        
        loc_matched = False
        if target_city and target_city in cand_text:
            score += 0.15
            loc_matched = True
        if target_state and (target_state in cand_text or f", {target_state}" in cand_text):
            score += 0.10
            loc_matched = True
        if loc_matched:
            reasons.append("Location match (city/state)")

        # Decision
        final_confidence = min(score, 1.0)
        is_match = final_confidence >= 0.45 or (target_domain and target_domain == cand_domain)

        return is_match, round(final_confidence * 100, 1), ", ".join(reasons)

    def match_social_profile(self, target_company: dict[str, Any], profile_url: str, profile_title: str, snippet: str) -> tuple[bool, int, str]:
        """
        Validates whether a social URL (LinkedIn, FB, IG) belongs to the company or decision maker.
        """
        target_name = (target_company.get("original_name") or "").lower()
        target_city = (target_company.get("original_city") or "").lower()
        target_state = (target_company.get("original_state") or "").lower()
        target_domain = self.extract_domain(target_company.get("original_website") or "")

        combined_text = f"{profile_url} {profile_title} {snippet}".lower()
        
        score = 0
        reasons = []

        # Domain in snippet/url
        if target_domain and target_domain in combined_text:
            score += 40
            reasons.append("Domain mentioned in profile")

        # Company name in profile title/URL
        name_words = [w for w in re.split(r'\W+', target_name) if len(w) > 3]
        matched_words = [w for w in name_words if w in combined_text]
        if len(matched_words) >= 2 or (len(name_words) == 1 and len(matched_words) == 1):
            score += 35
            reasons.append("Company name keywords present")

        # Location verification
        if target_city and target_city in combined_text:
            score += 15
            reasons.append("City match")
        if target_state and target_state in combined_text:
            score += 10
            reasons.append("State match")

        is_valid = score >= 50
        return is_valid, min(score, 100), ", ".join(reasons)

