from typing import Any

class PitchGenerator:
    """
    AI Personalized Cold Outreach Pitch Generator.
    Generates high-converting, personalized B2B outreach tailored for Tex Web Solutions Pvt. Ltd.
    """

    @staticmethod
    def generate_pitch(company_info: dict[str, Any], audit_info: dict[str, Any]) -> str:
        owner = company_info.get("owner_name") or company_info.get("primary_decision_maker")
        greeting = f"Hi {owner.split()[0]}," if owner else "Hi Team,"
        
        comp_name = company_info.get("official_name") or company_info.get("original_name") or "your business"
        city = company_info.get("city") or company_info.get("original_city") or "your area"
        state = company_info.get("state") or company_info.get("original_state") or ""
        loc_str = f" in {city}, {state}".strip() if city else ""

        cms = audit_info.get("tech_stack_cms", "Custom")
        has_ssl = audit_info.get("has_ssl", True)
        is_mobile = audit_info.get("is_mobile_responsive", True)
        score = audit_info.get("seo_audit_score", 70)
        has_analytics = audit_info.get("has_analytics", False)

        # Pain points
        pain_points = []
        if not is_mobile:
            pain_points.append("- Your website is not fully mobile-responsive, which causes over 60% of homeowners browsing on smartphones to bounce.")
        if not has_ssl:
            pain_points.append("- Your website is currently running without an SSL certificate ('Not Secure'), which lowers Google search rankings and customer trust.")
        if cms in ["Wix", "GoDaddy Builder"]:
            pain_points.append(f"- Your site is currently built on {cms}, which creates code bloat, slows load times, and limits custom conversion workflows.")
        if not has_analytics:
            pain_points.append("- You don't have active Google Analytics tracking installed, so you're missing data on where your local leads are coming from.")
        if not pain_points:
            pain_points.append(f"- Your current site has an overall web health score of {score}/100 and could capture significantly more high-intent local roofing leads with modern conversion rate optimization.")

        pain_points_text = "\n".join(pain_points)

        pitch = f"""Subject: Quick question regarding {comp_name}'s website{loc_str}

{greeting}

I was looking at roofing contractors{loc_str} and came across {comp_name}. Your customer reputation and craftsmanship look fantastic.

While browsing your website, I noticed a few quick technical opportunities that might be costing you local estimates:
{pain_points_text}

At Tex Web Solutions Pvt. Ltd., we specialize in building fast, high-converting websites, web applications, and SEO systems specifically tailored for contractors and service businesses.

Would you be open to a complimentary 3-minute video breakdown showing how a modern redesign could help {comp_name} outrank local competitors and generate more direct calls?

Best regards,

Tex Web Solutions Pvt. Ltd.
Web Design • Web Applications • SEO • Digital Solutions
https://texwebsolutions.com"""

        return pitch.strip()

