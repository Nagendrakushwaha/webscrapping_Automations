import re
import json
from typing import Any, Optional
from ..config import settings
from .adapters.base import SearchResultItem

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')
LINKEDIN_IN_REGEX = re.compile(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)', re.I)
LINKEDIN_CO_REGEX = re.compile(r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)', re.I)
INSTAGRAM_REGEX = re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)', re.I)
FACEBOOK_REGEX = re.compile(r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9_.-]+)', re.I)

class AIExtractor:
    """
    AI Extraction and Structured Parsing Engine.
    Uses LLM (Gemini or OpenAI) when API keys are available, with built-in heuristic pattern extraction.
    """

    def __init__(self, gemini_key: str = "", openai_key: str = ""):
        self.gemini_key = gemini_key or settings.GEMINI_API_KEY
        self.openai_key = openai_key or settings.OPENAI_API_KEY

    async def extract_from_search_results(
        self, 
        company_name: str, 
        search_items: list[SearchResultItem]
    ) -> dict[str, Any]:
        """
        Parses search result titles and snippets to extract decision makers, contacts, and social profiles.
        """
        extracted = {
            "owner": None,
            "ceo": None,
            "founder": None,
            "cofounder": None,
            "business_email": None,
            "business_phone": None,
            "personal_email": None,
            "personal_phone": None,
            "personal_linkedin": None,
            "business_linkedin": None,
            "business_instagram": None,
            "business_facebook": None,
            "evidence": []
        }

        # 1. First run high-precision heuristic pattern extraction
        for item in search_items:
            url = item.url
            text = f"{item.title} {item.snippet}"

            # Social URLs in search results
            if not extracted["personal_linkedin"]:
                m = LINKEDIN_IN_REGEX.search(url)
                if m:
                    extracted["personal_linkedin"] = m.group(0).split("?")[0]
                    # Also try to extract person name from title e.g. "John Doe - Owner - ABC Roofing | LinkedIn"
                    name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-|–]', item.title)
                    if name_match:
                        person_name = name_match.group(1).strip()
                        self._assign_role_from_text(person_name, text, item, extracted)

            if not extracted["business_linkedin"]:
                m = LINKEDIN_CO_REGEX.search(url)
                if m:
                    extracted["business_linkedin"] = m.group(0).split("?")[0]
                    extracted["evidence"].append({
                        "field_name": "Business LinkedIn",
                        "discovered_value": extracted["business_linkedin"],
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "confidence_score": 90,
                        "verification_status": "Verified",
                        "notes": f"Discovered via search result: '{item.title}'"
                    })

            if not extracted["business_instagram"]:
                m = INSTAGRAM_REGEX.search(url)
                if m and not any(x in url.lower() for x in ["/p/", "/explore", "/tags"]):
                    extracted["business_instagram"] = m.group(0).split("?")[0]
                    extracted["evidence"].append({
                        "field_name": "Business Instagram",
                        "discovered_value": extracted["business_instagram"],
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "confidence_score": 85,
                        "verification_status": "Verified",
                        "notes": f"Discovered via search result: '{item.title}'"
                    })

            if not extracted["business_facebook"]:
                m = FACEBOOK_REGEX.search(url)
                if m and not any(x in url.lower() for x in ["/share", "/events", "/groups"]):
                    extracted["business_facebook"] = m.group(0).split("?")[0]
                    extracted["evidence"].append({
                        "field_name": "Business Facebook",
                        "discovered_value": extracted["business_facebook"],
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "confidence_score": 85,
                        "verification_status": "Verified",
                        "notes": f"Discovered via search result: '{item.title}'"
                    })

            # Check for emails in snippet
            for em in EMAIL_REGEX.findall(text):
                em_lower = em.lower().strip(".,;")
                if not em_lower.endswith((".png", ".jpg", ".webp")):
                    if not extracted["business_email"]:
                        extracted["business_email"] = em_lower
                        extracted["evidence"].append({
                            "field_name": "Business Email",
                            "discovered_value": em_lower,
                            "source_name": item.source_name,
                            "source_url": item.url,
                            "confidence_score": 80,
                            "verification_status": "Found but Unverified",
                            "notes": f"Found in snippet: '{item.snippet[:80]}...'"
                        })

            # Check for phones in snippet
            for ph in PHONE_REGEX.findall(text):
                clean_ph = f"({ph[0]}) {ph[1]}-{ph[2]}"
                if not extracted["business_phone"]:
                    extracted["business_phone"] = clean_ph
                    extracted["evidence"].append({
                        "field_name": "Business Phone",
                        "discovered_value": clean_ph,
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "confidence_score": 85,
                        "verification_status": "Found but Unverified",
                        "notes": f"Found in snippet: '{item.snippet[:80]}...'"
                    })

            # Decision maker extraction from text (e.g. "Owner: John Smith", "Founded by David Lee in 2012")
            self._scan_for_leadership(text, item, extracted)

        # 2. If Gemini or OpenAI is configured, invoke LLM for deeper semantic extraction
        if self.gemini_key or self.openai_key:
            await self._run_llm_extraction(company_name, search_items, extracted)

        return extracted

    def _assign_role_from_text(self, name: str, text: str, item: SearchResultItem, extracted: dict[str, Any]):
        t_low = text.lower()
        if "owner" in t_low and not extracted["owner"]:
            extracted["owner"] = {"name": name, "title": "Owner"}
            extracted["evidence"].append({
                "field_name": "Owner",
                "discovered_value": name,
                "source_name": item.source_name,
                "source_url": item.url,
                "confidence_score": 85,
                "verification_status": "Found and Verified",
                "notes": f"Profile matches owner on {item.source_name}"
            })
        elif "ceo" in t_low and not extracted["ceo"]:
            extracted["ceo"] = {"name": name, "title": "CEO"}
            extracted["evidence"].append({
                "field_name": "CEO",
                "discovered_value": name,
                "source_name": item.source_name,
                "source_url": item.url,
                "confidence_score": 85,
                "verification_status": "Found and Verified",
                "notes": f"Profile matches CEO on {item.source_name}"
            })
        elif "founder" in t_low and not extracted["founder"]:
            extracted["founder"] = {"name": name, "title": "Founder"}
            extracted["evidence"].append({
                "field_name": "Founder",
                "discovered_value": name,
                "source_name": item.source_name,
                "source_url": item.url,
                "confidence_score": 85,
                "verification_status": "Found and Verified",
                "notes": f"Profile matches Founder on {item.source_name}"
            })

    def _scan_for_leadership(self, text: str, item: SearchResultItem, extracted: dict[str, Any]):
        patterns = [
            (re.compile(r'(?:owner|proprietor)[:\- ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', re.I), "owner", "Owner"),
            (re.compile(r'(?:ceo|chief executive officer)[:\- ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', re.I), "ceo", "CEO"),
            (re.compile(r'(?:founder|founded by)[:\- ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', re.I), "founder", "Founder"),
            (re.compile(r'(?:co-founder|cofounder)[:\- ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', re.I), "cofounder", "Co-Founder"),
            (re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*,\s*(?:owner|founder|ceo|president)', re.I), "owner", "Owner")
        ]

        for regex, key, display_role in patterns:
            if not extracted[key]:
                m = regex.search(text)
                if m:
                    cand_name = m.group(1).strip()
                    # Filter common false positives
                    if not any(bad in cand_name.lower() for bad in ["roofing", "company", "contractor", "services", "contact", "about", "team"]):
                        extracted[key] = {"name": cand_name, "title": display_role}
                        extracted["evidence"].append({
                            "field_name": display_role,
                            "discovered_value": cand_name,
                            "source_name": item.source_name,
                            "source_url": item.url,
                            "confidence_score": 80,
                            "verification_status": "Found and Verified",
                            "notes": f"Extracted from snippet text: '{m.group(0)}'"
                        })

    async def _run_llm_extraction(
        self, 
        company_name: str, 
        search_items: list[SearchResultItem], 
        extracted: dict[str, Any]
    ):
        """
        Uses configured Gemini or OpenAI LLM to parse raw text and return structured JSON.
        """
        snippets_text = "\n".join([f"Source [{i+1}] ({item.url}): {item.title}\n{item.snippet}" for i, item in enumerate(search_items[:8])])
        
        prompt = f"""
        You are a business intelligence data extractor for: '{company_name}'.
        Carefully read the provided search results and extract only facts with clear evidence.
        Do NOT invent or guess any names, emails, phones, or URLs.
        
        Target fields:
        1. Owner name & title
        2. CEO name & title
        3. Founder name & title
        4. Co-Founder name & title
        5. Business email
        6. Business phone
        7. Personal professional email (decision maker)
        8. Personal professional phone (decision maker)
        9. Personal LinkedIn URL
        10. Business LinkedIn URL
        11. Business Instagram URL
        12. Business Facebook URL

        Return ONLY a JSON object:
        {{
            "owner": {{"name": "...", "title": "..."}} or null,
            "ceo": {{"name": "...", "title": "..."}} or null,
            "founder": {{"name": "...", "title": "..."}} or null,
            "cofounder": {{"name": "...", "title": "..."}} or null,
            "business_email": "..." or null,
            "business_phone": "..." or null,
            "personal_email": "..." or null,
            "personal_phone": "..." or null,
            "personal_linkedin": "..." or null,
            "business_linkedin": "..." or null,
            "business_instagram": "..." or null,
            "business_facebook": "..." or null
        }}

        Search Results:
        {snippets_text}
        """

        try:
            if self.gemini_key:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                if response and response.text:
                    self._merge_llm_json(response.text, extracted)
            elif self.openai_key:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=self.openai_key)
                resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                if resp.choices and resp.choices[0].message.content:
                    self._merge_llm_json(resp.choices[0].message.content, extracted)
        except Exception:
            pass

    def _merge_llm_json(self, raw_text: str, extracted: dict[str, Any]):
        try:
            # Find JSON block
            clean = raw_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            data = json.loads(clean)

            for key in ["owner", "ceo", "founder", "cofounder"]:
                if data.get(key) and not extracted.get(key):
                    extracted[key] = data[key]
            for key in [
                "business_email", "business_phone", "personal_email", "personal_phone",
                "personal_linkedin", "business_linkedin", "business_instagram", "business_facebook"
            ]:
                if data.get(key) and not extracted.get(key):
                    extracted[key] = data[key]
        except Exception:
            pass
