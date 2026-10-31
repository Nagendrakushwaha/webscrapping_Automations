import re
from bs4 import BeautifulSoup
from typing import Any

class TechStackAuditor:
    """
    Website Technology Stack, SEO Audit & Redesign Opportunity Analyzer.
    Provides actionable sales ammunition for Tex Web Solutions Pvt. Ltd.
    """

    @staticmethod
    def audit_html(html: str, url: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        html_lower = html.lower()

        # 1. CMS & Tech Stack Detection
        cms = "Custom / Other"
        if "wp-content" in html_lower or "wp-includes" in html_lower:
            cms = "WordPress"
        elif "wix.com" in html_lower or "parastorage.com" in html_lower:
            cms = "Wix"
        elif "squarespace.com" in html_lower:
            cms = "Squarespace"
        elif "webflow.com" in html_lower or "data-wf-site" in html_lower:
            cms = "Webflow"
        elif "cdn.shopify.com" in html_lower:
            cms = "Shopify"
        elif "godaddy" in html_lower or "secureserver.net" in html_lower:
            cms = "GoDaddy Builder"
        elif "__next" in html_lower or "next.js" in html_lower:
            cms = "Next.js (Modern Web App)"
        elif "react" in html_lower and "root" in html_lower:
            cms = "React SPA"

        # 2. SSL Status
        has_ssl = url.lower().startswith("https://")

        # 3. Mobile Responsiveness Check
        viewport_tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
        is_mobile_responsive = bool(viewport_tag and "width=" in (viewport_tag.get("content", "").lower()))

        # 4. Analytics & Tracking Pixels
        has_analytics = any(x in html_lower for x in [
            "googletagmanager.com", "google-analytics.com", "gtag(", "ga('create'", "fbevents.js", "fbq("
        ])

        # 5. SEO Hygiene
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        has_seo_title = 15 <= len(title_text) <= 70

        desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        has_meta_desc = bool(desc_tag and len(desc_tag.get("content", "").strip()) >= 30)

        og_tag = soup.find("meta", property=re.compile(r"^og:image$", re.I))
        has_og_image = bool(og_tag)

        # 6. Overall SEO & Website Health Score (0 to 100)
        score = 0
        if has_ssl: score += 25
        if is_mobile_responsive: score += 25
        if has_seo_title: score += 15
        if has_meta_desc: score += 15
        if has_analytics: score += 10
        if has_og_image: score += 10

        # 7. Redesign Opportunity Assessment for Tex Web Solutions
        if score < 50 or not is_mobile_responsive or not has_ssl or cms in ["GoDaddy Builder", "Wix"]:
            redesign_opportunity = "High (Critical Redesign Candidate)"
        elif score < 80:
            redesign_opportunity = "Medium (SEO & Conversion Upgrade)"
        else:
            redesign_opportunity = "Low (Modern Site)"

        return {
            "tech_stack_cms": cms,
            "has_ssl": has_ssl,
            "is_mobile_responsive": is_mobile_responsive,
            "has_analytics": has_analytics,
            "seo_audit_score": score,
            "redesign_opportunity": redesign_opportunity,
            "title_text": title_text,
            "has_meta_desc": has_meta_desc
        }

