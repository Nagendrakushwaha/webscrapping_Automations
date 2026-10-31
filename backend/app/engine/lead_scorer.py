from typing import Any
from ..models import Company

class LeadScorer:
    """
    Lead Opportunity & Deal Qualification Scoring Engine (0 to 100).
    Tailored for Tex Web Solutions Pvt. Ltd. to evaluate conversion readiness and website redesign viability.
    """

    @staticmethod
    def calculate_score(company: Company) -> tuple[int, str]:
        score = 10
        reasons = []

        # 1. Decision Maker Availability (up to +25)
        if company.owner_name:
            score += 25
            reasons.append(f"+25 Owner identified ({company.owner_name})")
        elif company.ceo_name or company.founder_name:
            score += 20
            dm = company.ceo_name or company.founder_name
            reasons.append(f"+20 Key executive identified ({dm})")
        elif company.primary_decision_maker:
            score += 15
            reasons.append(f"+15 Decision maker identified ({company.primary_decision_maker})")

        # 2. Verified Contact Information (up to +25)
        if company.email_verification_status == "Valid":
            score += 20
            provider_str = f" via {company.email_mailbox_provider}" if company.email_mailbox_provider else ""
            reasons.append(f"+20 Deliverable MX-verified email{provider_str}")
        elif company.business_email:
            score += 10
            reasons.append("+10 Business email discovered")

        if company.business_phone:
            line_str = f" ({company.phone_line_type})" if company.phone_line_type else ""
            score += 10
            reasons.append(f"+10 Active phone number{line_str}")

        # 3. Agency Redesign Opportunity (up to +30)
        # Higher score means higher probability of closing a deal for Tex Web Solutions
        if company.redesign_opportunity and company.redesign_opportunity.startswith("High"):
            score += 25
            reasons.append("+25 Critical redesign candidate (High client demand)")
        elif company.website_status in ["No Official Website", "Broken", "N/A"]:
            score += 25
            reasons.append("+25 Missing/Broken website (Immediate web development opportunity)")
        elif company.redesign_opportunity and company.redesign_opportunity.startswith("Medium"):
            score += 15
            reasons.append("+15 Medium redesign candidate (SEO / Conversion optimization needed)")

        if not company.has_ssl and company.website_status == "Active":
            score += 10
            reasons.append("+10 Unsecured HTTP (Google search ranking risk)")

        if not company.is_mobile_responsive and company.website_status == "Active":
            score += 10
            reasons.append("+10 Non-mobile responsive (High visitor bounce rate)")

        # 4. Social & Professional Presence (up to +10)
        if company.personal_linkedin:
            score += 10
            reasons.append("+10 Direct personal LinkedIn connection")
        elif company.business_linkedin or company.business_facebook:
            score += 5
            reasons.append("+5 Active business social presence")

        # Cap between 0 and 100
        final_score = min(max(score, 0), 100)
        reason_summary = " • ".join(reasons) if reasons else "Base discovery score"

        return final_score, reason_summary
