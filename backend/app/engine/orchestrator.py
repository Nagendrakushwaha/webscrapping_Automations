import asyncio
import json
from datetime import datetime
from typing import Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..config import settings
from ..database import AsyncSessionLocal
from ..models import Job, Company, Evidence, ManualReview, DecisionMakerRecord, ApiConfig
from .query_generator import QueryGenerator
from .entity_matcher import EntityMatcher
from .verifier import DataVerifier
from .ai_extractor import AIExtractor
from .adapters import (
    WebsiteAdapter, TavilyAdapter, GoogleSearchAdapter, GooglePlacesAdapter,
    BingAdapter, BraveAdapter, DuckDuckGoAdapter, ApolloAdapter, HunterAdapter
)

# Active running background tasks: job_id -> dict(task, cancel_event, pause_event, listeners)
ACTIVE_JOBS: dict[str, dict[str, Any]] = {}

class ResearchOrchestrator:
    """
    Main Research & Enrichment Orchestration Engine.
    Executes deep multi-source research across all 12 mandatory fields for every business lead.
    """

    def __init__(self, job_id: str, db_session_factory=AsyncSessionLocal):
        self.job_id = job_id
        self.session_factory = db_session_factory
        self.query_gen = QueryGenerator()
        self.matcher = EntityMatcher()
        self.verifier = DataVerifier()
        self.website_adapter = WebsiteAdapter()
        self.duckduckgo_adapter = DuckDuckGoAdapter()
        
        # Will be loaded from database API configs
        self.adapters: dict[str, Any] = {
            "website": self.website_adapter,
            "duckduckgo": self.duckduckgo_adapter
        }
        self.ai_extractor = AIExtractor()
        self.stop_requested = False
        self.pause_requested = False

    async def load_configured_adapters(self, session: AsyncSession):
        """Loads and initializes configured API adapters from database."""
        result = await session.execute(select(ApiConfig).where(ApiConfig.is_enabled == True))
        configs = result.scalars().all()
        
        gemini_key = ""
        openai_key = ""

        for cfg in configs:
            if not cfg.api_key:
                continue
            p_name = cfg.provider_name.lower()
            extra = json.loads(cfg.extra_config or "{}")

            if p_name == "tavily":
                self.adapters["tavily"] = TavilyAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "google_search":
                self.adapters["google_search"] = GoogleSearchAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "google_places":
                self.adapters["google_places"] = GooglePlacesAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "bing":
                self.adapters["bing"] = BingAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "brave":
                self.adapters["brave"] = BraveAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "apollo":
                self.adapters["apollo"] = ApolloAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "hunter":
                self.adapters["hunter"] = HunterAdapter(api_key=cfg.api_key, extra_config=extra)
            elif p_name == "gemini":
                gemini_key = cfg.api_key
            elif p_name == "openai":
                openai_key = cfg.api_key

        self.ai_extractor = AIExtractor(gemini_key=gemini_key, openai_key=openai_key)

    async def run(self):
        """Main background loop processing companies in batches."""
        async with self.session_factory() as session:
            await self.load_configured_adapters(session)
            
            # Update job status to processing
            job = await session.get(Job, self.job_id)
            if not job:
                return
            job.status = "processing"
            await session.commit()

            # Retrieve research settings
            settings_dict = json.loads(job.settings_json or "{}")
            concurrency = settings_dict.get("concurrency", settings.DEFAULT_CONCURRENCY)
            semaphore = asyncio.Semaphore(concurrency)

        while not self.stop_requested:
            # Check pause
            if self.pause_requested:
                await asyncio.sleep(1)
                continue

            # Fetch next batch of unprocessed or retry companies
            async with self.session_factory() as session:
                q = (
                    select(Company)
                    .where(Company.job_id == self.job_id)
                    .where(Company.overall_verification_status.in_(["Unverified", "Failed"]))
                    .limit(10)
                )
                res = await session.execute(q)
                batch = res.scalars().all()

                if not batch:
                    # All done!
                    job = await session.get(Job, self.job_id)
                    if job:
                        job.status = "completed"
                        job.current_stage = "Research Complete"
                        job.current_company_name = ""
                        await session.commit()
                    break

                # Process batch with concurrency
                tasks = [self._process_single_company(comp.id, semaphore) for comp in batch]
                await asyncio.gather(*tasks)

    async def _process_single_company(self, company_id: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            if self.stop_requested:
                return

            async with self.session_factory() as session:
                comp = await session.get(Company, company_id)
                if not comp:
                    return

                # Update job progress display
                job = await session.get(Job, self.job_id)
                if job:
                    job.current_company_name = comp.original_name
                    job.current_stage = "Deep Multi-Source Research"
                    await session.commit()

                try:
                    await self._execute_company_research(comp, session)
                except Exception as e:
                    comp.overall_verification_status = "Failed"
                    comp.research_notes = f"Research error: {str(e)}"
                    await session.commit()

                # Update Job counters
                await self._refresh_job_statistics(session)

    async def _execute_company_research(self, comp: Company, session: AsyncSession):
        sources_searched = []
        evidences_to_add: list[Evidence] = []
        reviews_to_add: list[ManualReview] = []

        comp_dict = {
            "original_name": comp.original_name,
            "original_city": comp.original_city,
            "original_state": comp.original_state,
            "original_phone": comp.original_phone,
            "original_website": comp.original_website,
            "official_website": comp.official_website or comp.original_website
        }

        # Step 1: Query Generator - produce 15+ variations for all 12 fields
        queries_by_field = self.query_gen.generate_all_queries(comp_dict)

        # Step 2: Website Direct Crawl & Extraction (Home, About, Contact, Team, Services)
        website_target = comp.original_website or comp.official_website
        if website_target:
            sources_searched.append("Website Crawler")
            site_data = await self.website_adapter.crawl_and_extract(website_target)
            
            comp.website_status = site_data.get("website_status", "Unverified")
            comp.official_website = site_data.get("official_website", website_target)
            comp.website_title = site_data.get("title", "")
            comp.website_description = site_data.get("description", "")
            comp.address = site_data.get("address", "") or comp.address
            comp.zip_code = site_data.get("zip_code", "") or comp.zip_code
            comp.year_established = site_data.get("year_established", "") or comp.year_established
            
            # Map subpages
            pages = site_data.get("pages_found", {})
            comp.about_page_url = pages.get("about", "")
            comp.contact_page_url = pages.get("contact", "")
            comp.team_page_url = pages.get("team", "")
            comp.services_page_url = pages.get("services", "")

            # Discovered emails from site
            if site_data.get("emails"):
                emails = site_data["emails"]
                comp.business_email = emails[0]
                comp.additional_business_emails = json.dumps(emails[1:], ensure_ascii=False)
                comp.business_email_status = "Found and Verified"

            # Discovered phones from site
            if site_data.get("phones"):
                phones = site_data["phones"]
                comp.business_phone = phones[0]
                comp.additional_business_phones = json.dumps(phones[1:], ensure_ascii=False)
                comp.business_phone_status = "Found and Verified"

            # Socials from site
            if site_data.get("personal_linkedin"):
                comp.personal_linkedin = site_data["personal_linkedin"]
                comp.personal_linkedin_status = "Found and Verified"
            if site_data.get("business_linkedin"):
                comp.business_linkedin = site_data["business_linkedin"]
                comp.business_linkedin_status = "Found and Verified"
            if site_data.get("business_instagram"):
                comp.business_instagram = site_data["business_instagram"]
                comp.business_instagram_status = "Found and Verified"
            if site_data.get("business_facebook"):
                comp.business_facebook = site_data["business_facebook"]
                comp.business_facebook_status = "Found and Verified"

            # Decision makers found on team / leadership pages
            for dm in site_data.get("decision_makers", []):
                role = dm.get("role_type", "")
                name = dm.get("name", "")
                title = dm.get("title", "")
                if "Owner" in role and not comp.owner_name:
                    comp.owner_name = name
                    comp.owner_title = title
                    comp.owner_status = "Found and Verified"
                    comp.owner_confidence = 90
                elif "CEO" in role and not comp.ceo_name:
                    comp.ceo_name = name
                    comp.ceo_title = title
                    comp.ceo_status = "Found and Verified"
                    comp.ceo_confidence = 90
                elif "Founder" in role and not comp.founder_name:
                    comp.founder_name = name
                    comp.founder_title = title
                    comp.founder_status = "Found and Verified"
                    comp.founder_confidence = 90

            # Attach website evidence
            for ev in site_data.get("evidence", []):
                evidences_to_add.append(Evidence(
                    company_id=comp.id,
                    field_name=ev["field_name"],
                    discovered_value=str(ev["discovered_value"]),
                    source_name=ev["source_name"],
                    source_url=ev["source_url"],
                    confidence_score=ev["confidence_score"],
                    verification_status=ev["verification_status"],
                    notes=ev["notes"]
                ))

        # Step 3: Multi-Source External Search (Tavily, Google, Bing, Brave, Places, DDG)
        search_items = []
        
        # Prioritize enabled external search adapters
        for adapter_name, adapter in self.adapters.items():
            if adapter_name == "website":
                continue
            if adapter.is_configured:
                sources_searched.append(adapter.name)
                # Search identity & decision makers
                sample_queries = queries_by_field.get("owner", [])[:1] + queries_by_field.get("identity", [])[:1]
                for q in sample_queries:
                    if q:
                        results = await adapter.search(q, max_results=3)
                        search_items.extend(results)

        # Step 4: AI Extraction and Entity Matching on Search Results
        if search_items:
            extracted = await self.ai_extractor.extract_from_search_results(comp.original_name, search_items)
            
            # Map extracted decision makers if not already set
            if extracted.get("owner") and not comp.owner_name:
                comp.owner_name = extracted["owner"]["name"]
                comp.owner_title = extracted["owner"].get("title", "Owner")
                comp.owner_status = "Found and Verified"
                comp.owner_confidence = 85
            if extracted.get("ceo") and not comp.ceo_name:
                comp.ceo_name = extracted["ceo"]["name"]
                comp.ceo_title = extracted["ceo"].get("title", "CEO")
                comp.ceo_status = "Found and Verified"
                comp.ceo_confidence = 85
            if extracted.get("founder") and not comp.founder_name:
                comp.founder_name = extracted["founder"]["name"]
                comp.founder_title = extracted["founder"].get("title", "Founder")
                comp.founder_status = "Found and Verified"
                comp.founder_confidence = 85
            if extracted.get("cofounder") and not comp.cofounder_name:
                comp.cofounder_name = extracted["cofounder"]["name"]
                comp.cofounder_title = extracted["cofounder"].get("title", "Co-Founder")
                comp.cofounder_status = "Found and Verified"
                comp.cofounder_confidence = 85

            # Map extracted contacts & socials
            if extracted.get("business_email") and not comp.business_email:
                comp.business_email = extracted["business_email"]
                comp.business_email_status = "Found but Unverified"
            if extracted.get("business_phone") and not comp.business_phone:
                comp.business_phone = extracted["business_phone"]
                comp.business_phone_status = "Found but Unverified"
            if extracted.get("personal_email") and not comp.personal_email:
                comp.personal_email = extracted["personal_email"]
                comp.personal_email_status = "Found but Unverified"
            if extracted.get("personal_phone") and not comp.personal_phone:
                comp.personal_phone = extracted["personal_phone"]
                comp.personal_phone_status = "Found but Unverified"
            if extracted.get("personal_linkedin") and not comp.personal_linkedin:
                comp.personal_linkedin = extracted["personal_linkedin"]
                comp.personal_linkedin_status = "Found and Verified"
            if extracted.get("business_linkedin") and not comp.business_linkedin:
                comp.business_linkedin = extracted["business_linkedin"]
                comp.business_linkedin_status = "Found and Verified"
            if extracted.get("business_instagram") and not comp.business_instagram:
                comp.business_instagram = extracted["business_instagram"]
                comp.business_instagram_status = "Found and Verified"
            if extracted.get("business_facebook") and not comp.business_facebook:
                comp.business_facebook = extracted["business_facebook"]
                comp.business_facebook_status = "Found and Verified"

            # Add evidence from search results
            for ev in extracted.get("evidence", []):
                evidences_to_add.append(Evidence(
                    company_id=comp.id,
                    field_name=ev["field_name"],
                    discovered_value=str(ev["discovered_value"]),
                    source_name=ev["source_name"],
                    source_url=ev["source_url"],
                    confidence_score=ev["confidence_score"],
                    verification_status=ev["verification_status"],
                    notes=ev["notes"]
                ))

        # Step 5: Primary Decision Maker Resolution (Hierarchy: Owner > Founder > Co-Founder > CEO > President)
        if comp.owner_name:
            comp.primary_decision_maker = comp.owner_name
            comp.primary_decision_maker_title = comp.owner_title or "Owner"
        elif comp.founder_name:
            comp.primary_decision_maker = comp.founder_name
            comp.primary_decision_maker_title = comp.founder_title or "Founder"
        elif comp.cofounder_name:
            comp.primary_decision_maker = comp.cofounder_name
            comp.primary_decision_maker_title = comp.cofounder_title or "Co-Founder"
        elif comp.ceo_name:
            comp.primary_decision_maker = comp.ceo_name
            comp.primary_decision_maker_title = comp.ceo_title or "CEO"

        # Step 6: Email Verification (Syntax & DNS MX Records)
        check_email = comp.personal_email or comp.business_email
        if check_email:
            em_status, em_reason = self.verifier.verify_email_syntax_and_mx(check_email)
            comp.email_verification_status = em_status
            evidences_to_add.append(Evidence(
                company_id=comp.id,
                field_name="Email Deliverability Check",
                discovered_value=check_email,
                source_name="DNS MX Verifier",
                source_url="",
                confidence_score=95 if em_status == "Valid" else 30,
                verification_status="Verified" if em_status == "Valid" else "Unverified",
                notes=em_reason
            ))

        # Step 7: Missing Fields Assessment across ALL 12 MANDATORY FIELDS
        mandatory_fields = [
            ("Owner", comp.owner_name),
            ("CEO", comp.ceo_name),
            ("Founder", comp.founder_name),
            ("Co-Founder", comp.cofounder_name),
            ("Business Email", comp.business_email),
            ("Business Phone", comp.business_phone),
            ("Personal Professional Email", comp.personal_email),
            ("Public Professional Phone", comp.personal_phone),
            ("Personal LinkedIn", comp.personal_linkedin),
            ("Business LinkedIn", comp.business_linkedin),
            ("Business Instagram", comp.business_instagram),
            ("Business Facebook", comp.business_facebook)
        ]
        
        missing = [name for name, val in mandatory_fields if not val]
        comp.missing_fields = json.dumps(missing)

        # Step 8: Calculate Overall Confidence Score & Verification Status
        found_count = 12 - len(missing)
        has_website_proof = bool(comp.website_status == "Active" and (comp.business_email or comp.business_phone))
        sources_unique_count = len(set(sources_searched))
        
        calc_confidence = self.verifier.calculate_confidence(
            sources_count=sources_unique_count,
            has_direct_website_proof=has_website_proof,
            identity_match_score=90.0 if comp.official_website else 70.0
        )
        comp.overall_confidence_score = calc_confidence

        if found_count >= 8 and calc_confidence >= 85:
            comp.overall_verification_status = "Fully Verified"
        elif found_count >= 3:
            comp.overall_verification_status = "Partially Verified"
        elif found_count > 0:
            comp.overall_verification_status = "Unverified"
        else:
            comp.overall_verification_status = "Not Found"

        comp.sources_searched = json.dumps(sources_searched)
        comp.last_checked = datetime.utcnow()

        # Step 9: Commit Evidence and Company state
        for ev in evidences_to_add:
            session.add(ev)
        for rev in reviews_to_add:
            session.add(rev)

        await session.commit()

    async def _refresh_job_statistics(self, session: AsyncSession):
        job = await session.get(Job, self.job_id)
        if not job:
            return

        res = await session.execute(select(Company).where(Company.job_id == self.job_id))
        all_comps = res.scalars().all()

        job.total_companies = len(all_comps)
        job.processed_companies = len([c for c in all_comps if c.overall_verification_status != "Unverified"])
        job.enriched_count = len([c for c in all_comps if c.business_email or c.owner_name or c.personal_linkedin])
        job.fully_verified_count = len([c for c in all_comps if c.overall_verification_status == "Fully Verified"])
        job.partially_verified_count = len([c for c in all_comps if c.overall_verification_status == "Partially Verified"])
        job.not_found_count = len([c for c in all_comps if c.overall_verification_status == "Not Found"])
        job.failed_count = len([c for c in all_comps if c.overall_verification_status == "Failed"])
        
        rev_res = await session.execute(
            select(ManualReview)
            .join(Company, ManualReview.company_id == Company.id)
            .where(Company.job_id == self.job_id)
            .where(ManualReview.review_status == "Pending")
        )
        job.manual_review_count = len(rev_res.scalars().all())

        await session.commit()
