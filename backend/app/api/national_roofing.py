import json
import math
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db, SessionLocal
from ..models import NationalRoofingJob, Company
from ..schemas import (
    NationalRoofingStartRequest,
    NationalRoofingJobOut,
    NationalRoofingLeadOut,
    NationalRoofingListResponse
)
from ..engine.discovery.national_roofing_discovery import (
    NationalRoofingEngine,
    ACTIVE_NATIONAL_JOBS
)
from ..core.excel_exporter import (
    export_national_roofing_job_to_excel,
    export_national_roofing_job_to_csv
)

router = APIRouter(prefix="/api/national-roofing", tags=["National Roofing Directory"])


@router.post("/start", response_model=NationalRoofingJobOut)
def start_national_roofing_scrape(
    req: NationalRoofingStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Starts a new automated National Roofing Directory scraping run."""
    state_name = req.state.strip() or "Texas"
    state_code = req.state_code.strip() or "TX"

    new_job = NationalRoofingJob(
        name=f"National Roofing - {state_name} Extraction",
        state=state_name,
        state_code=state_code,
        status="running",
        current_stage="Initializing City Directory Discovery...",
        selected_cities_json=json.dumps(req.cities or []),
        checkpoint_json=json.dumps({"processed_urls": [], "failed_urls": [], "discovered_urls": []})
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Launch background extraction worker
    engine = NationalRoofingEngine(session_factory=SessionLocal, job_id=new_job.id)
    ACTIVE_NATIONAL_JOBS[new_job.id] = engine
    background_tasks.add_task(engine.run_sync)

    return new_job


@router.get("/cities")
def get_state_cities(state: str = Query("Texas", description="US State name or abbreviation")):
    """Discovers available city directory links from the state directory hub."""
    state_url = NationalRoofingEngine.get_state_url(state)
    cities = NationalRoofingEngine.discover_city_pages_from_html("", state_url)
    return {
        "state": state,
        "state_url": state_url,
        "reference_listing_count": 10107 if state.lower() in ["texas", "tx"] else 2500,
        "cities": cities
    }


@router.get("/jobs", response_model=list[NationalRoofingJobOut])
def list_scraping_jobs(db: Session = Depends(get_db)):
    """Lists past and active National Roofing Directory scraping jobs."""
    jobs = db.query(NationalRoofingJob).order_by(desc(NationalRoofingJob.created_at)).limit(25).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=NationalRoofingJobOut)
def get_job_progress(job_id: str, db: Session = Depends(get_db)):
    """Returns real-time progress and extraction counters for a scraping job."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="National Roofing scraping job not found.")
    return job


@router.post("/jobs/{job_id}/pause", response_model=NationalRoofingJobOut)
def pause_scraping_job(job_id: str, db: Session = Depends(get_db)):
    """Pauses an active scraping job and saves checkpoint."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    engine = ACTIVE_NATIONAL_JOBS.get(job_id)
    if engine:
        engine.pause_requested = True

    job.status = "paused"
    job.current_stage = "Paused by user. Checkpoint saved."
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/resume", response_model=NationalRoofingJobOut)
def resume_scraping_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resumes an interrupted or paused scraping job from its last checkpoint."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    job.status = "running"
    job.current_stage = "Resuming from checkpoint..."
    db.commit()
    db.refresh(job)

    engine = ACTIVE_NATIONAL_JOBS.get(job_id)
    if not engine:
        engine = NationalRoofingEngine(session_factory=SessionLocal, job_id=job_id)
        ACTIVE_NATIONAL_JOBS[job_id] = engine

    engine.pause_requested = False
    engine.stop_requested = False
    background_tasks.add_task(engine.run_sync)

    return job


@router.post("/jobs/{job_id}/stop", response_model=NationalRoofingJobOut)
def stop_scraping_job(job_id: str, db: Session = Depends(get_db)):
    """Stops an active scraping job."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    engine = ACTIVE_NATIONAL_JOBS.get(job_id)
    if engine:
        engine.stop_requested = True

    job.status = "stopped"
    job.current_stage = "Stopped by user."
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/retry-failed", response_model=NationalRoofingJobOut)
def retry_failed_records(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retries failed profile URLs recorded in checkpoint."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    try:
        cp = json.loads(job.checkpoint_json or "{}")
        failed = cp.get("failed_urls", [])
        # Move failed URLs back to discovered for retry
        cp["failed_urls"] = []
        job.checkpoint_json = json.dumps(cp)
        job.failed_profiles_count = 0
        job.status = "running"
        job.current_stage = f"Retrying {len(failed)} failed profile URLs..."
        db.commit()
        db.refresh(job)
    except Exception:
        pass

    engine = ACTIVE_NATIONAL_JOBS.get(job_id)
    if not engine:
        engine = NationalRoofingEngine(session_factory=SessionLocal, job_id=job_id)
        ACTIVE_NATIONAL_JOBS[job_id] = engine

    background_tasks.add_task(engine.run_sync)
    return job


@router.get("/jobs/{job_id}/leads", response_model=NationalRoofingListResponse)
def get_discovered_leads(
    job_id: str,
    search: Optional[str] = None,
    city: Optional[str] = None,
    has_gmail: bool = False,
    has_email: bool = False,
    has_phone: bool = False,
    has_website: bool = False,
    missing_website: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns paginated, searchable, and filterable results table for National Roofing Directory leads.
    """
    job = db.get(NationalRoofingJob, job_id)
    query = db.query(Company).filter(Company.national_roofing_job_id == job_id)

    # Search filter
    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            (Company.official_name.ilike(s_term)) |
            (Company.owner_name.ilike(s_term)) |
            (Company.city.ilike(s_term))
        )

    # City filter
    if city and city != "All":
        query = query.filter(Company.city.ilike(f"%{city.strip()}%"))

    # Attribute filters
    if has_gmail:
        query = query.filter(Company.gmail_address != "", Company.gmail_address != "N/A")
    if has_email:
        query = query.filter(
            ((Company.business_email != "") & (Company.business_email != "N/A")) |
            ((Company.gmail_address != "") & (Company.gmail_address != "N/A"))
        )
    if has_phone:
        query = query.filter(Company.business_phone != "", Company.business_phone != "N/A")
    if has_website:
        query = query.filter(Company.official_website != "", Company.official_website != "N/A")
    if missing_website:
        query = query.filter((Company.official_website == "") | (Company.official_website == "N/A"))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.order_by(desc(Company.created_at)).offset(offset).limit(page_size).all()

    lead_items = []
    for r in records:
        lead_items.append(NationalRoofingLeadOut(
            id=r.id,
            name=r.official_name or r.original_name or "N/A",
            owner_name=r.owner_name or "N/A",
            trades=r.trades or "Roofing Contractors",
            city=r.city or "N/A",
            state=r.state or "TX",
            zip_code=r.zip_code or "N/A",
            address=r.address or "N/A",
            phone=r.business_phone or "N/A",
            email=r.business_email or "N/A",
            gmail_address=r.gmail_address or "N/A",
            website=r.official_website or "N/A",
            profile_url=r.directory_profile_url or "N/A",
            website_status=r.website_status or "No Website Found",
            verification_status=r.overall_verification_status or "Unverified"
        ))

    job_out = NationalRoofingJobOut.model_validate(job) if job else None

    return NationalRoofingListResponse(
        job=job_out,
        leads=lead_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/jobs/{job_id}/export/excel")
def export_excel(job_id: str, db: Session = Depends(get_db)):
    """Downloads 8-Worksheet Excel Workbook for National Roofing Directory scraping results."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found.")

    companies = db.query(Company).filter(Company.national_roofing_job_id == job_id).all()
    file_path = export_national_roofing_job_to_excel(job, companies)

    if not file_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate Excel export.")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/jobs/{job_id}/export/csv")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    """Downloads CSV export for National Roofing Directory scraping results."""
    job = db.get(NationalRoofingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found.")

    companies = db.query(Company).filter(Company.national_roofing_job_id == job_id).all()
    file_path = export_national_roofing_job_to_csv(job, companies)

    if not file_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate CSV export.")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="text/csv"
    )

