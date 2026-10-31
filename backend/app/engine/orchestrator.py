import asyncio
import json
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import select
from ..config import settings
from ..database import SessionLocal
from ..models import Job, Company, Evidence, ManualReview, ApiConfig
from .query_generator import QueryGenerator
from .entity_matcher import EntityMatcher
from .verifier import DataVerifier
from .ai_extractor import AIExtractor
from .tech_auditor import TechStackAuditor
from .pitch_generator import PitchGenerator
from .adapters import (
    WebsiteAdapter, TavilyAdapter, GoogleSearchAdapter, GooglePlacesAdapter,
    BingAdapter, BraveAdapter, DuckDuckGoAdapter, ApolloAdapter, HunterAdapter,
    StateRegistryAdapter
)

ACTIVE_JOBS: dict[str, dict[str, Any]] = {}

class ResearchOrchestrator:
    """
    Main Research & Enrichment Orchestration Engine.
    Executes deep multi-source research across all 12 mandatory fields for every business lead.
    """

    def __init__(self, job_id: str, db_session_factory=SessionLocal):
        self.job_id = job_id
        self.session_factory = db_session_factory
        self.query_gen = QueryGenerator()
        self.matcher = EntityMatcher()
        self.verifier = DataVerifier()
        self.website_adapter = WebsiteAdapter()
        self.duckduckgo_adapter = DuckDuckGoAdapter()
        self.state_registry_adapter = StateRegistryAdapter()
        
        self.adapters: dict[str, Any] = {
            "website": self.website_adapter,
            "duckduckgo": self.duckduckgo_adapter,
            "state_registry": self.state_registry_adapter
        }
        self.ai_extractor = AIExtractor()
        self.stop_requested = False
        self.pause_requested = False

    def load_configured_adapters(self, session):
        """Loads and initializes configured API adapters from database."""
        configs = session.query(ApiConfig).filter(ApiConfig.is_enabled == True).all()
        
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

    def run_sync(self):
        """Synchronous runner compatible with FastAPI BackgroundTasks and offline testing."""
        with self.session_factory() as session:
            self.load_configured_adapters(session)
            job = session.get(Job, self.job_id)
            if not job:
                return
            job.status = "processing"
            session.commit()

        while not self.stop_requested:
            if self.pause_requested:
                import time
                time.sleep(1)
                continue

            with self.session_factory() as session:
                batch = (
                    session.query(Company)
                    .filter(Company.job_id == self.job_id)
                    .filter(Company.overall_verification_status.in_(["Unverified", "Failed"]))
                    .limit(10)
                    .all()
                )

                if not batch:
                    job = session.get(Job, self.job_id)
                    if job:
                        job.status = "completed"
                        job.current_stage = "Research Complete"
                        job.current_company_name = ""
                        session.commit()
                    break

                for comp in batch:
                    if self.stop_requested:
                        break
                    job = session.get(Job, self.job_id)
                    if job:
                        job.current_company_name = comp.original_name
                        job.current_stage = "Deep Multi-Source Research"
                        session.commit()

                    try:
                        self.execute_company_research_sync(comp, session)
                    except Exception as e:
                        comp.overall_verification_status = "Failed"
                        comp.research_notes = f"Research error: {str(e)}"
                        session.commit()

                    self._refresh_job_statistics(session)

    def execute_company_research_sync(self, comp: Company, session):
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

        # Step 1: Query Generator
        queries_by_field = self.query_gen.generate_all_queries(comp_dict)

        # Step 2: Website Direct Crawl & Extraction
        website_target = comp.original_website or comp.official_website
        if website_target:
            sources_searched.append("Website Crawler")
            site_data = self.website_adapter.crawl_and_extract_sync(website_target)
            
            comp.website_status = site_data.get("website_status", "Unverified")
            comp.official_website = site_data.get("official_website", website_target)
            comp.website_title = site_data.get("title", "")
            comp.website_description = site_data.get("description", "")
            comp.address = site_data.get("address", "") or comp.address
            comp.zip_code = site_data.get("zip_code", "") or comp.zip_code
            comp.year_established = site_data.get("year_established", "") or comp.year_established
            
            pages = site_data.get("pages_found", {})
            comp.about_page_url = pages.get("about", "")
            comp.contact_page_url = pages.get("contact", "")
            comp.team_page_url = pages.get("team", "")
            comp.services_page_url = pages.get("services", "")

            if site_data.get("emails"):
                emails = site_data["emails"]
                comp.business_email = emails[0]
                comp.additional_business_emails = json.dumps(emails[1:], ensure_ascii=False)
                comp.business_email_status = "Found and Verified"

            if site_data.get("phones"):
                phones = site_data["phones"]
                comp.business_phone = phones[0]
                comp.additional_business_phones = json.dumps(phones[1:], ensure_ascii=False)
                comp.business_phone_status = "Found and Verified"

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

        # Step 2.5: US State Business Registry Lookup (SOS Filing for Owner/Officers)
        if not comp.owner_name:
            state_code = comp.original_state or ""
            officers = self.state_registry_adapter.lookup_officers_sync(comp.original_name, state_code)
            if officers:
                first_officer = officers[0]
                comp.owner_name = first_officer["name"]
                comp.owner_title = first_officer.get("title", "Registered Agent / Owner")
                comp.owner_status = "Found and Verified"
                comp.owner_confidence = 85
                sources_searched.append(first_officer["source_name"])
                evidences_to_add.append(Evidence(
                    company_id=comp.id,
                    field_name="Owner / Officer (State Filing)",
                    discovered_value=first_officer["name"],
                    source_name=first_officer["source_name"],
                    source_url=first_officer.get("source_url", ""),
                    confidence_score=85,
                    verification_status="Verified",
                    notes=f"Discovered via Secretary of State corporate registration as {first_officer.get('role_type', 'Officer')}."
                ))

        # Step 3: Primary Decision Maker Resolution
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

        # Step 4: Email Verification & Mailbox Provider Detection
        check_email = comp.personal_email or comp.business_email
        if check_email:
            em_status, em_reason, em_provider = self.verifier.verify_email_syntax_and_mx(check_email)
            comp.email_verification_status = em_status
            comp.email_mailbox_provider = em_provider
            evidences_to_add.append(Evidence(
                company_id=comp.id,
                field_name="Email Deliverability Check",
                discovered_value=check_email,
                source_name="DNS MX Verifier",
                source_url="",
                confidence_score=95 if em_status == "Valid" else 30,
                verification_status="Verified" if em_status == "Valid" else "Unverified",
                notes=f"{em_reason} [Provider: {em_provider}]"
            ))

        # Step 4.5: Phone Line-Type Classification
        check_phone = comp.business_phone or comp.original_phone or comp.personal_phone
        if check_phone:
            comp.phone_line_type = self.verifier.classify_phone_line_type(check_phone)

        # Step 4.6: Tech Stack, SEO Hygiene Audit & Personalized Pitch for Tex Web Solutions
        raw_html = site_data.get("raw_html", "") if 'site_data' in locals() and site_data else ""
        audit_results = TechStackAuditor.audit_html(raw_html, comp.official_website or website_target or "")
        comp.tech_stack_cms = audit_results["tech_stack_cms"]
        comp.has_ssl = audit_results["has_ssl"]
        comp.is_mobile_responsive = audit_results["is_mobile_responsive"]
        comp.has_analytics = audit_results["has_analytics"]
        comp.seo_audit_score = audit_results["seo_audit_score"]
        comp.redesign_opportunity = audit_results["redesign_opportunity"]

        comp_dict_pitch = {
            "owner_name": comp.owner_name,
            "primary_decision_maker": comp.primary_decision_maker,
            "official_name": comp.official_name or comp.original_name,
            "original_name": comp.original_name,
            "city": comp.original_city,
            "state": comp.original_state
        }
        comp.ai_personalized_pitch = PitchGenerator.generate_pitch(comp_dict_pitch, audit_results)

        # Step 5: Missing Fields Assessment across ALL 12 MANDATORY FIELDS
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

        # Step 6: Calculate Overall Confidence Score & Verification Status
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

        for ev in evidences_to_add:
            session.add(ev)
        for rev in reviews_to_add:
            session.add(rev)

        session.commit()

    async def run(self):
        """Main background loop processing companies in batches."""
        with self.session_factory() as session:
            self.load_configured_adapters(session)
            job = session.get(Job, self.job_id)
            if not job:
                return
            job.status = "processing"
            session.commit()

            settings_dict = json.loads(job.settings_json or "{}")
            concurrency = settings_dict.get("concurrency", settings.DEFAULT_CONCURRENCY)
            semaphore = asyncio.Semaphore(concurrency)

        while not self.stop_requested:
            if self.pause_requested:
                await asyncio.sleep(1)
                continue

            with self.session_factory() as session:
                batch = (
                    session.query(Company)
                    .filter(Company.job_id == self.job_id)
                    .filter(Company.overall_verification_status.in_(["Unverified", "Failed"]))
                    .limit(10)
                    .all()
                )

                if not batch:
                    job = session.get(Job, self.job_id)
                    if job:
                        job.status = "completed"
                        job.current_stage = "Research Complete"
                        job.current_company_name = ""
                        session.commit()
                    break

                batch_ids = [c.id for c in batch]

            tasks = [self._process_single_company(cid, semaphore) for cid in batch_ids]
            await asyncio.gather(*tasks)

    async def _process_single_company(self, company_id: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            if self.stop_requested:
                return

            with self.session_factory() as session:
                comp = session.get(Company, company_id)
                if not comp:
                    return

                job = session.get(Job, self.job_id)
                if job:
                    job.current_company_name = comp.original_name
                    job.current_stage = "Deep Multi-Source Research"
                    session.commit()

                try:
                    await self._execute_company_research(comp, session)
                except Exception as e:
                    comp.overall_verification_status = "Failed"
                    comp.research_notes = f"Research error: {str(e)}"
                    session.commit()

                self._refresh_job_statistics(session)

    async def _execute_company_research(self, comp: Company, session):
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

        # Step 1: Query Generator
        queries_by_field = self.query_gen.generate_all_queries(comp_dict)

        # Step 2: Website Direct Crawl & Extraction
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
            
            pages = site_data.get("pages_found", {})
            comp.about_page_url = pages.get("about", "")
            comp.contact_page_url = pages.get("contact", "")
            comp.team_page_url = pages.get("team", "")
            comp.services_page_url = pages.get("services", "")

            if site_data.get("emails"):
                emails = site_data["emails"]
                comp.business_email = emails[0]
                comp.additional_business_emails = json.dumps(emails[1:], ensure_ascii=False)
                comp.business_email_status = "Found and Verified"

            if site_data.get("phones"):
                phones = site_data["phones"]
                comp.business_phone = phones[0]
                comp.additional_business_phones = json.dumps(phones[1:], ensure_ascii=False)
                comp.business_phone_status = "Found and Verified"

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

        # Step 3: Multi-Source External Search
        search_items = []
        for adapter_name, adapter in self.adapters.items():
            if adapter_name == "website":
                continue
            if adapter.is_configured:
                sources_searched.append(adapter.name)
                sample_queries = queries_by_field.get("owner", [])[:1] + queries_by_field.get("identity", [])[:1]
                for q in sample_queries:
                    if q:
                        results = await adapter.search(q, max_results=3)
                        search_items.extend(results)

        # Step 4: AI Extraction and Entity Matching
        if search_items:
            extracted = await self.ai_extractor.extract_from_search_results(comp.original_name, search_items)
            
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

        # Step 4.5: US State Business Registry Lookup (SOS Filing for Owner/Officers)
        if not comp.owner_name:
            state_code = comp.original_state or ""
            officers = self.state_registry_adapter.lookup_officers_sync(comp.original_name, state_code)
            if officers:
                first_officer = officers[0]
                comp.owner_name = first_officer["name"]
                comp.owner_title = first_officer.get("title", "Registered Agent / Owner")
                comp.owner_status = "Found and Verified"
                comp.owner_confidence = 85
                sources_searched.append(first_officer["source_name"])
                evidences_to_add.append(Evidence(
                    company_id=comp.id,
                    field_name="Owner / Officer (State Filing)",
                    discovered_value=first_officer["name"],
                    source_name=first_officer["source_name"],
                    source_url=first_officer.get("source_url", ""),
                    confidence_score=85,
                    verification_status="Verified",
                    notes=f"Discovered via Secretary of State corporate registration as {first_officer.get('role_type', 'Officer')}."
                ))

        # Step 5: Primary Decision Maker Resolution
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

        # Step 6: Email Verification & Mailbox Provider Detection
        check_email = comp.personal_email or comp.business_email
        if check_email:
            em_status, em_reason, em_provider = self.verifier.verify_email_syntax_and_mx(check_email)
            comp.email_verification_status = em_status
            comp.email_mailbox_provider = em_provider
            evidences_to_add.append(Evidence(
                company_id=comp.id,
                field_name="Email Deliverability Check",
                discovered_value=check_email,
                source_name="DNS MX Verifier",
                source_url="",
                confidence_score=95 if em_status == "Valid" else 30,
                verification_status="Verified" if em_status == "Valid" else "Unverified",
                notes=f"{em_reason} [Provider: {em_provider}]"
            ))

        # Step 6.5: Phone Line-Type Classification
        check_phone = comp.business_phone or comp.original_phone or comp.personal_phone
        if check_phone:
            comp.phone_line_type = self.verifier.classify_phone_line_type(check_phone)

        # Step 6.6: Tech Stack, SEO Hygiene Audit & Personalized Pitch for Tex Web Solutions
        raw_html = site_data.get("raw_html", "") if 'site_data' in locals() and site_data else ""
        audit_results = TechStackAuditor.audit_html(raw_html, comp.official_website or website_target or "")
        comp.tech_stack_cms = audit_results["tech_stack_cms"]
        comp.has_ssl = audit_results["has_ssl"]
        comp.is_mobile_responsive = audit_results["is_mobile_responsive"]
        comp.has_analytics = audit_results["has_analytics"]
        comp.seo_audit_score = audit_results["seo_audit_score"]
        comp.redesign_opportunity = audit_results["redesign_opportunity"]

        comp_dict_pitch = {
            "owner_name": comp.owner_name,
            "primary_decision_maker": comp.primary_decision_maker,
            "official_name": comp.official_name or comp.original_name,
            "original_name": comp.original_name,
            "city": comp.original_city,
            "state": comp.original_state
        }
        comp.ai_personalized_pitch = PitchGenerator.generate_pitch(comp_dict_pitch, audit_results)

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

        session.commit()

    def _refresh_job_statistics(self, session):
        job = session.get(Job, self.job_id)
        if not job:
            return

        all_comps = session.query(Company).filter(Company.job_id == self.job_id).all()

        job.total_companies = len(all_comps)
        job.processed_companies = len([c for c in all_comps if c.overall_verification_status != "Unverified"])
        job.enriched_count = len([c for c in all_comps if c.business_email or c.owner_name or c.personal_linkedin])
        job.fully_verified_count = len([c for c in all_comps if c.overall_verification_status == "Fully Verified"])
        job.partially_verified_count = len([c for c in all_comps if c.overall_verification_status == "Partially Verified"])
        job.not_found_count = len([c for c in all_comps if c.overall_verification_status == "Not Found"])
        job.failed_count = len([c for c in all_comps if c.overall_verification_status == "Failed"])
        
        job.manual_review_count = (
            session.query(ManualReview)
            .join(Company, ManualReview.company_id == Company.id)
            .filter(Company.job_id == self.job_id)
            .filter(ManualReview.review_status == "Pending")
            .count()
        )

        session.commit()
