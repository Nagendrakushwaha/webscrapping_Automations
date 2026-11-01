import json
import time
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import AutomationJob, Job, Company
from ..core.location_service import LocationService
from .discovery.discovery_orchestrator import BusinessDiscoveryEngine
from .discovery.base import DiscoveredLead
from .orchestrator import ResearchOrchestrator
from .lead_scorer import LeadScorer

# Global in-memory registry of active automation workers for control
ACTIVE_AUTOMATIONS: dict[str, Any] = {}

class AutomationWorker:
    """
    Automated Lead Generation & Continuous Enrichment Worker.
    Executes automated geographic business discovery and feeds discovered leads
    directly into the deep 12-field enrichment engine with opportunity scoring.
    """

    def __init__(self, automation_id: str, db_session_factory=SessionLocal):
        self.automation_id = automation_id
        self.session_factory = db_session_factory
        self.stop_requested = False
        self.pause_requested = False

    def run_sync(self):
        """Main synchronous background worker loop."""
        ACTIVE_AUTOMATIONS[self.automation_id] = self

        with self.session_factory() as session:
            auto_job = session.get(AutomationJob, self.automation_id)
            if not auto_job:
                return

            auto_job.status = "running"
            auto_job.start_time = datetime.utcnow()
            auto_job.current_stage = "Initializing Geographic Zones & Discovery Adapters"
            session.commit()

            config = json.loads(auto_job.search_config_json or "{}")
            selected_states = config.get("states", ["TX"])
            selected_cities = config.get("cities", []) # list of city names or IDs
            search_mode = config.get("search_mode", "city_radius") # single_city, multi_city, entire_state, city_radius
            radius_miles = float(config.get("radius_miles", 50.0))
            industries = config.get("industries", ["Roofing Contractors"])
            target_leads = int(config.get("target_leads", 100))

            # 1. Resolve geographic target locations
            target_locations: list[dict[str, Any]] = []

            if search_mode in ["entire_state", "multi_state"] or not selected_cities:
                # Load major coverage hubs for each selected state
                all_cities = LocationService.get_cities_for_states(session, selected_states)
                for c in all_cities:
                    target_locations.append({
                        "city": c["city_name"],
                        "state": c["state_abbr"],
                        "lat": c["latitude"],
                        "lon": c["longitude"]
                    })
            else:
                # Resolve specific selected cities
                for city_item in selected_cities:
                    if isinstance(city_item, dict):
                        target_locations.append(city_item)
                    elif isinstance(city_item, str):
                        # Find city in DB
                        c_match = LocationService.search_cities(session, query=city_item, limit=1)
                        if c_match:
                            target_locations.append({
                                "city": c_match[0]["city_name"],
                                "state": c_match[0]["state_abbr"],
                                "lat": c_match[0]["latitude"],
                                "lon": c_match[0]["longitude"]
                            })

            if not target_locations:
                # Fallback to state capital or default city
                for st in selected_states:
                    st_obj = LocationService.get_state(session, st)
                    if st_obj:
                        target_locations.append({
                            "city": st_obj["capital"],
                            "state": st_obj["abbr"],
                            "lat": st_obj["latitude"],
                            "lon": st_obj["longitude"]
                        })

        # 2. Initialize Business Discovery Engine
        enabled_providers = config.get("providers") or ["the_roofing_list", "openstreetmap", "search_engines", "google_places"]
        with self.session_factory() as session:
            discovery_engine = BusinessDiscoveryEngine(session=session, enabled_providers=enabled_providers)

        def on_discovery_progress(prog_data: dict[str, Any]):
            with self.session_factory() as session:
                j = session.get(AutomationJob, self.automation_id)
                if j:
                    j.current_state = prog_data.get("current_state", j.current_state)
                    j.current_city = prog_data.get("current_city", j.current_city)
                    j.current_industry = prog_data.get("current_industry", j.current_industry)
                    j.current_provider = prog_data.get("current_provider", j.current_provider)
                    j.current_stage = prog_data.get("current_stage", j.current_stage)
                    j.total_discovered = prog_data.get("total_discovered", j.total_discovered)
                    j.unique_discovered = prog_data.get("unique_discovered", j.unique_discovered)
                    j.duplicate_count = prog_data.get("duplicate_count", j.duplicate_count)
                    session.commit()

        # Execute Discovery
        discovered_leads: list[DiscoveredLead] = discovery_engine.discover_leads(
            industries=industries,
            locations=target_locations,
            radius_miles=radius_miles,
            target_count=target_leads,
            on_progress=on_discovery_progress
        )

        # 3. Create Corresponding Parent Job for Unified System Visibility
        parent_job_id = None
        with self.session_factory() as session:
            auto_job = session.get(AutomationJob, self.automation_id)
            if auto_job:
                p_job = Job(
                    filename=f"Automated_{auto_job.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    total_companies=len(discovered_leads),
                    status="processing"
                )
                session.add(p_job)
                session.flush()
                parent_job_id = p_job.id
                auto_job.job_id = p_job.id
                auto_job.unique_discovered = len(discovered_leads)
                auto_job.current_stage = f"Discovered {len(discovered_leads)} unique businesses. Beginning Enrichment..."
                session.commit()

        # 4. Insert Discovered Leads into Company table
        company_ids = []
        with self.session_factory() as session:
            for idx, lead in enumerate(discovered_leads, start=1):
                comp = Company(
                    job_id=parent_job_id,
                    automation_id=self.automation_id,
                    original_id=f"AUTO-{idx:04d}",
                    original_name=lead.name,
                    original_trades=lead.trade or lead.industry,
                    original_city=lead.city,
                    original_state=lead.state,
                    original_phone=lead.phone,
                    original_website=lead.website,
                    original_claimed="Automated Discovery",
                    official_name=lead.name,
                    trades=lead.trade or lead.industry,
                    city=lead.city,
                    state=lead.state,
                    country=lead.country,
                    address=lead.address,
                    zip_code=lead.zip_code,
                    official_website=lead.website,
                    business_phone=lead.phone,
                    latitude=lead.latitude,
                    longitude=lead.longitude,
                    distance_from_center_miles=lead.distance_miles,
                    google_places_id=lead.provider_place_id,
                    discovery_provider=lead.provider,
                    directory_profile_url=lead.directory_profile_url,
                    directory_description=lead.directory_description,
                    business_description=lead.directory_description or "",
                    overall_verification_status="Unverified"
                )
                session.add(comp)
                session.flush()
                company_ids.append(comp.id)
            session.commit()

        # 5. Continuous Deep Enrichment using ResearchOrchestrator
        enricher = ResearchOrchestrator(parent_job_id, db_session_factory=self.session_factory)
        
        for cid in company_ids:
            if self.stop_requested:
                break
            while self.pause_requested:
                time.sleep(1)

            with self.session_factory() as session:
                comp = session.get(Company, cid)
                auto_job = session.get(AutomationJob, self.automation_id)
                if not comp or not auto_job:
                    continue

                auto_job.current_stage = f"Enriching: {comp.original_name} in {comp.original_city}, {comp.original_state}"
                session.commit()

                try:
                    # Run full 12-field research, tech audit, SOS corporate registry & AI pitch
                    enricher.execute_company_research_sync(comp, session)

                    # Calculate Opportunity Lead Score (0 to 100)
                    score, reasons = LeadScorer.calculate_score(comp)
                    comp.lead_score = score
                    comp.lead_score_reason = reasons

                    # Update automation statistics
                    auto_job.total_enriched += 1
                    if comp.email_verification_status == "Valid":
                        auto_job.verified_emails_count += 1

                    session.commit()
                except Exception as e:
                    auto_job.failed_count += 1
                    errs = json.loads(auto_job.error_log or "[]")
                    errs.append(f"{comp.original_name}: {str(e)}")
                    auto_job.error_log = json.dumps(errs[-50:]) # keep last 50
                    session.commit()

        # 6. Finalize Automation Job State
        with self.session_factory() as session:
            auto_job = session.get(AutomationJob, self.automation_id)
            p_job = session.get(Job, parent_job_id) if parent_job_id else None
            
            if auto_job:
                if self.stop_requested:
                    auto_job.status = "stopped"
                    auto_job.current_stage = "Automation Stopped by User"
                else:
                    auto_job.status = "completed"
                    auto_job.current_stage = "Automation & Enrichment Completed Successfully"
                auto_job.end_time = datetime.utcnow()
                session.commit()

            if p_job:
                p_job.status = "completed" if not self.stop_requested else "stopped"
                enricher._refresh_job_statistics(session)

        ACTIVE_AUTOMATIONS.pop(self.automation_id, None)

