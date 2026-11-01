import json
import threading
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models import AutomationJob, Company, SavedSearchConfig
from ..engine.automation_orchestrator import AutomationWorker, ACTIVE_AUTOMATIONS

router = APIRouter(prefix="/api/automation", tags=["Automated Lead Generation"])

class AutomationStartRequest(BaseModel):
    name: str = "US Lead Discovery Run"
    states: list[str] = Field(default_factory=lambda: ["TX"])
    cities: list[Any] = Field(default_factory=list)
    search_mode: str = "city_radius" # single_city, multi_city, entire_state, multi_state, city_radius
    radius_miles: float = 50.0
    industries: list[str] = Field(default_factory=lambda: ["Roofing Contractors"])
    target_leads: int = 50
    filters: dict[str, Any] = Field(default_factory=dict)

class ControlRequest(BaseModel):
    action: str # pause, resume, stop, retry

class SavedConfigRequest(BaseModel):
    name: str
    config: dict[str, Any]

@router.post("/start")
def start_automation(
    req: AutomationStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Launches an automated location-based business discovery and enrichment background job.
    """
    config_dict = {
        "states": req.states,
        "cities": req.cities,
        "search_mode": req.search_mode,
        "radius_miles": req.radius_miles,
        "industries": req.industries,
        "target_leads": req.target_leads,
        "filters": req.filters
    }

    auto_job = AutomationJob(
        name=req.name,
        status="pending",
        search_config_json=json.dumps(config_dict, ensure_ascii=False),
        total_target=req.target_leads,
        current_stage="Queued for Automated Geographic Discovery"
    )
    db.add(auto_job)
    db.commit()
    db.refresh(auto_job)

    # Launch background worker
    worker = AutomationWorker(automation_id=auto_job.id, db_session_factory=SessionLocal)
    background_tasks.add_task(worker.run_sync)

    return {
        "success": True,
        "automation_id": auto_job.id,
        "name": auto_job.name,
        "status": auto_job.status,
        "message": "Automated Lead Generation worker initiated successfully."
    }

@router.get("/jobs")
@router.get("/history")
def list_automation_jobs(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Returns list of all active and historic automation jobs with run statistics.
    """
    jobs = db.query(AutomationJob).order_by(AutomationJob.created_at.desc()).limit(limit).all()
    results = []
    for j in jobs:
        results.append({
            "id": j.id,
            "name": j.name,
            "status": j.status,
            "current_stage": j.current_stage,
            "current_state": j.current_state,
            "current_city": j.current_city,
            "current_industry": j.current_industry,
            "current_provider": j.current_provider,
            "total_target": j.total_target,
            "total_discovered": j.total_discovered,
            "unique_discovered": j.unique_discovered,
            "duplicate_count": j.duplicate_count,
            "total_enriched": j.total_enriched,
            "verified_emails_count": j.verified_emails_count,
            "failed_count": j.failed_count,
            "job_id": j.job_id,
            "search_config": json.loads(j.search_config_json or "{}"),
            "discovered_count": j.total_discovered,
            "enriched_count": j.total_enriched,
            "target_leads": j.total_target,
            "progress_percentage": int((j.total_enriched / j.total_target * 100)) if j.total_target > 0 else 0,
            "decision_makers_found": j.total_enriched,
            "verified_emails_found": j.verified_emails_count,
            "start_time": j.start_time.isoformat() if j.start_time else None,
            "end_time": j.end_time.isoformat() if j.end_time else None,
            "created_at": j.created_at.isoformat() if j.created_at else None
        })
    return {"history": results, "jobs": results, "total": len(results)}

@router.get("/jobs/{job_id}")
@router.get("/{job_id}")
def get_automation_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves real-time status, counters, and logs for a specific automation run.
    """
    j = db.get(AutomationJob, job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Automation job not found")

    return {
        "id": j.id,
        "name": j.name,
        "status": j.status,
        "current_stage": j.current_stage,
        "current_state": j.current_state,
        "current_city": j.current_city,
        "current_industry": j.current_industry,
        "current_provider": j.current_provider,
        "total_target": j.total_target,
        "target_leads": j.total_target,
        "total_discovered": j.total_discovered,
        "discovered_count": j.total_discovered,
        "unique_discovered": j.unique_discovered,
        "duplicate_count": j.duplicate_count,
        "total_enriched": j.total_enriched,
        "enriched_count": j.total_enriched,
        "progress_percentage": int((j.total_enriched / j.total_target * 100)) if j.total_target > 0 else 0,
        "verified_emails_count": j.verified_emails_count,
        "verified_emails_found": j.verified_emails_count,
        "decision_makers_found": j.total_enriched,
        "failed_count": j.failed_count,
        "job_id": j.job_id,
        "search_config": json.loads(j.search_config_json or "{}"),
        "error_log": json.loads(j.error_log or "[]"),
        "start_time": j.start_time.isoformat() if j.start_time else None,
        "end_time": j.end_time.isoformat() if j.end_time else None
    }

@router.post("/jobs/{job_id}/control")
def control_automation_job(
    job_id: str,
    req: ControlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Controls an active automation run: pause, resume, stop, or retry.
    """
    j = db.get(AutomationJob, job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Automation job not found")

    action = req.action.lower().strip()
    worker: Optional[AutomationWorker] = ACTIVE_AUTOMATIONS.get(job_id)

    if action == "pause":
        if worker:
            worker.pause_requested = True
        j.status = "paused"
        j.current_stage = "Automation Paused by User"
        db.commit()
    elif action == "resume":
        if worker:
            worker.pause_requested = False
        j.status = "running"
        j.current_stage = "Resuming Automated Research..."
        db.commit()
    elif action == "stop":
        if worker:
            worker.stop_requested = True
        j.status = "stopped"
        j.current_stage = "Automation Stopped by User"
        j.end_time = datetime.utcnow()
        db.commit()
    elif action == "retry" or action == "retry-failed":
        new_worker = AutomationWorker(automation_id=job_id, db_session_factory=SessionLocal)
        background_tasks.add_task(new_worker.run_sync)
        j.status = "running"
        j.current_stage = "Retrying Failed Records..."
        db.commit()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    return {"success": True, "job_id": job_id, "status": j.status, "action": action}

@router.post("/{job_id}/pause")
def pause_automation(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return control_automation_job(job_id, ControlRequest(action="pause"), background_tasks, db)

@router.post("/{job_id}/resume")
def resume_automation(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return control_automation_job(job_id, ControlRequest(action="resume"), background_tasks, db)

@router.post("/{job_id}/stop")
def stop_automation(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return control_automation_job(job_id, ControlRequest(action="stop"), background_tasks, db)

@router.post("/{job_id}/retry-failed")
def retry_failed_automation(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return control_automation_job(job_id, ControlRequest(action="retry"), background_tasks, db)

@router.get("/jobs/{job_id}/leads")
@router.get("/{job_id}/leads")
def get_automation_leads(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    industry: Optional[str] = None,
    city: Optional[str] = None,
    has_owner: Optional[bool] = None,
    has_email: Optional[bool] = None,
    min_score: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Returns paginated discovered and enriched business leads for this automation run.
    """
    q = db.query(Company).filter(Company.automation_id == job_id)

    if industry:
        q = q.filter(Company.trades.ilike(f"%{industry}%"))
    if city:
        q = q.filter(Company.city.ilike(f"%{city}%"))
    if has_owner is True:
        q = q.filter(Company.owner_name != "")
    if has_email is True:
        q = q.filter(Company.business_email != "")
    if min_score is not None:
        q = q.filter(Company.lead_score >= min_score)

    total = q.count()
    leads = q.order_by(Company.lead_score.desc(), Company.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        "leads": [
            {
                "id": c.id,
                "name": c.official_name or c.original_name,
                "industry": c.trades or c.original_trades,
                "city": c.city or c.original_city,
                "state": c.state or c.original_state,
                "website": c.official_website or c.original_website,
                "website_status": c.website_status,
                "phone": c.business_phone or c.original_phone,
                "phone_line_type": c.phone_line_type,
                "email": c.business_email,
                "email_status": c.email_verification_status,
                "mailbox_provider": c.email_mailbox_provider,
                "owner_name": c.owner_name,
                "owner_title": c.owner_title or "Owner",
                "ceo_name": c.ceo_name,
                "founder_name": c.founder_name,
                "primary_decision_maker": c.primary_decision_maker,
                "personal_email": c.personal_email,
                "personal_phone": c.personal_phone,
                "personal_linkedin": c.personal_linkedin,
                "business_linkedin": c.business_linkedin,
                "business_instagram": c.business_instagram,
                "business_facebook": c.business_facebook,
                "tech_stack_cms": c.tech_stack_cms,
                "has_ssl": c.has_ssl,
                "is_mobile_responsive": c.is_mobile_responsive,
                "seo_audit_score": c.seo_audit_score,
                "redesign_opportunity": c.redesign_opportunity,
                "lead_score": c.lead_score,
                "lead_score_reason": c.lead_score_reason,
                "lead_status": c.lead_status or "New",
                "is_starred": bool(c.is_starred),
                "website_screenshot_url": c.website_screenshot_url or "",
                "ai_personalized_pitch": c.ai_personalized_pitch,
                "confidence_score": c.overall_confidence_score,
                "verification_status": c.overall_verification_status,
                "distance_miles": c.distance_from_center_miles,
                "directory_profile_url": c.directory_profile_url,
                "directory_description": c.directory_description,
                "provider": c.discovery_provider
            }
            for c in leads
        ]
    }

@router.get("/saved-configs")
def get_saved_configs(db: Session = Depends(get_db)):
    """Returns saved search configurations."""
    configs = db.query(SavedSearchConfig).order_by(SavedSearchConfig.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "config": json.loads(c.config_json or "{}"),
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in configs
    ]

@router.post("/saved-configs")
def save_config(req: SavedConfigRequest, db: Session = Depends(get_db)):
    """Saves a search configuration for quick re-use."""
    obj = SavedSearchConfig(
        name=req.name,
        config_json=json.dumps(req.config, ensure_ascii=False)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"success": True, "id": obj.id, "name": obj.name}
