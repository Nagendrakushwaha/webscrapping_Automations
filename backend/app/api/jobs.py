import os
import shutil
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..config import UPLOAD_DIR
from ..database import get_db, SessionLocal
from ..models import Job, Company
from ..schemas import JobOut, JobControlRequest, PreviewResponse, ColumnMappingRequest
from ..core.excel_parser import parse_and_preview, read_all_companies
from ..engine.orchestrator import ResearchOrchestrator, ACTIVE_JOBS

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/preview", response_model=PreviewResponse)
@router.post("/upload-preview", response_model=PreviewResponse)
def upload_file_and_preview(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, and .xls files are supported.")

    file_id = f"upload_{os.urandom(8).hex()}"
    saved_path = UPLOAD_DIR / f"{file_id}{ext}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        preview_data = parse_and_preview(saved_path, file.filename or "leads_upload")
        preview_data["file_id"] = f"{file_id}{ext}"
        if "original_headers" not in preview_data:
            preview_data["original_headers"] = preview_data["headers"]
        return preview_data
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@router.post("/upload", response_model=JobOut)
def upload_file_and_start_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: str = Form("{}"),
    db: Session = Depends(get_db)
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, and .xls files are supported.")

    file_id = f"upload_{os.urandom(8).hex()}{ext}"
    saved_path = UPLOAD_DIR / file_id

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        mappings = json.loads(column_mapping) if column_mapping else {}
    except Exception:
        mappings = {}

    if not mappings:
        try:
            preview = parse_and_preview(saved_path, file.filename or "leads_upload")
            mappings = preview.get("detected_mappings", {})
        except Exception:
            mappings = {}

    companies_data = read_all_companies(saved_path, mappings)
    if not companies_data:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=400, detail="No companies found in uploaded file.")

    new_job = Job(
        filename=file.filename or file_id,
        total_companies=len(companies_data),
        processed_companies=0,
        status="pending",
        current_stage="Initialized",
        column_mapping_json=json.dumps(mappings),
        settings_json=json.dumps({})
    )
    db.add(new_job)
    db.flush()

    for comp_dict in companies_data:
        comp = Company(
            job_id=new_job.id,
            original_id=comp_dict["original_id"],
            original_name=comp_dict["original_name"],
            original_trades=comp_dict["original_trades"],
            original_city=comp_dict["original_city"],
            original_state=comp_dict["original_state"],
            original_phone=comp_dict["original_phone"],
            original_website=comp_dict["original_website"],
            original_claimed=comp_dict["original_claimed"],
            raw_data_json=comp_dict["raw_data_json"],
            official_name=comp_dict["original_name"],
            official_website=comp_dict["original_website"],
            city=comp_dict["original_city"],
            state=comp_dict["original_state"],
            trades=comp_dict["original_trades"],
            overall_verification_status="Unverified"
        )
        db.add(comp)

    db.commit()
    db.refresh(new_job)

    # Launch background orchestrator using FastAPI BackgroundTasks thread pool
    orchestrator = ResearchOrchestrator(new_job.id, SessionLocal)
    ACTIVE_JOBS[new_job.id] = {
        "orchestrator": orchestrator
    }
    background_tasks.add_task(orchestrator.run_sync)

    return new_job

@router.post("/start-research", response_model=JobOut)
def start_research_job(
    req: ColumnMappingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    file_path = UPLOAD_DIR / req.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found or expired.")

    companies_data = read_all_companies(file_path, req.mappings)
    if not companies_data:
        raise HTTPException(status_code=400, detail="No companies found in uploaded file.")

    new_job = Job(
        filename=req.file_id,
        total_companies=len(companies_data),
        processed_companies=0,
        status="pending",
        current_stage="Initialized",
        column_mapping_json=json.dumps(req.mappings),
        settings_json=json.dumps(req.settings or {})
    )
    db.add(new_job)
    db.flush()

    for comp_dict in companies_data:
        comp = Company(
            job_id=new_job.id,
            original_id=comp_dict["original_id"],
            original_name=comp_dict["original_name"],
            original_trades=comp_dict["original_trades"],
            original_city=comp_dict["original_city"],
            original_state=comp_dict["original_state"],
            original_phone=comp_dict["original_phone"],
            original_website=comp_dict["original_website"],
            original_claimed=comp_dict["original_claimed"],
            raw_data_json=comp_dict["raw_data_json"],
            official_name=comp_dict["original_name"],
            official_website=comp_dict["original_website"],
            city=comp_dict["original_city"],
            state=comp_dict["original_state"],
            trades=comp_dict["original_trades"],
            overall_verification_status="Unverified"
        )
        db.add(comp)

    db.commit()
    db.refresh(new_job)

    # Launch background orchestrator using FastAPI BackgroundTasks thread pool
    orchestrator = ResearchOrchestrator(new_job.id, SessionLocal)
    ACTIVE_JOBS[new_job.id] = {
        "orchestrator": orchestrator
    }
    background_tasks.add_task(orchestrator.run_sync)

    return new_job

@router.get("/{job_id}", response_model=JobOut)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    pct = 0.0
    if job.total_companies > 0:
        pct = round((job.processed_companies / job.total_companies) * 100, 1)
    
    res = JobOut.model_validate(job)
    res.progress_percentage = pct
    return res

@router.post("/{job_id}/control", response_model=JobOut)
def control_job(job_id: str, req: JobControlRequest, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    active_entry = ACTIVE_JOBS.get(job_id)

    if req.action == "pause":
        if active_entry:
            active_entry["orchestrator"].pause_requested = True
        job.status = "paused"
        job.current_stage = "Paused by user"
    elif req.action == "resume":
        if active_entry:
            active_entry["orchestrator"].pause_requested = False
        else:
            orchestrator = ResearchOrchestrator(job_id, SessionLocal)
            task = asyncio.create_task(orchestrator.run())
            ACTIVE_JOBS[job_id] = {"orchestrator": orchestrator, "task": task}
        job.status = "processing"
        job.current_stage = "Resumed"
    elif req.action == "stop":
        if active_entry:
            active_entry["orchestrator"].stop_requested = True
        job.status = "stopped"
        job.current_stage = "Stopped by user"
    elif req.action == "retry_failed":
        failed_comps = db.query(Company).filter(Company.job_id == job_id, Company.overall_verification_status == "Failed").all()
        for c in failed_comps:
            c.overall_verification_status = "Unverified"
        db.commit()

        if not active_entry or active_entry["task"].done():
            orchestrator = ResearchOrchestrator(job_id, SessionLocal)
            task = asyncio.create_task(orchestrator.run())
            ACTIVE_JOBS[job_id] = {"orchestrator": orchestrator, "task": task}
        job.status = "processing"
        job.current_stage = "Retrying failed companies"

    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(desc(Job.created_at)).limit(20).all()
    out = []
    for j in jobs:
        pct = round((j.processed_companies / j.total_companies) * 100, 1) if j.total_companies > 0 else 0.0
        m = JobOut.model_validate(j)
        m.progress_percentage = pct
        out.append(m)
    return out
