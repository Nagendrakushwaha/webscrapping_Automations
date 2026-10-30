import os
import shutil
import json
import asyncio
from pathlib import Path
from typing import Any
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..config import UPLOAD_DIR
from ..database import get_db, AsyncSessionLocal
from ..models import Job, Company, ApiConfig
from ..schemas import JobOut, JobControlRequest, PreviewResponse, ColumnMappingRequest
from ..core.excel_parser import parse_and_preview, read_all_companies
from ..engine.orchestrator import ResearchOrchestrator, ACTIVE_JOBS

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/upload-preview", response_model=PreviewResponse)
async def upload_file_and_preview(file: UploadFile = File(...)):
    """
    Accepts XLSX or CSV upload, validates structure, detects columns, and returns a preview.
    """
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
        return preview_data
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@router.post("/start-research", response_model=JobOut)
async def start_research_job(
    req: ColumnMappingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirms column mappings, inserts all leads with raw preservation, and launches background research.
    """
    file_path = UPLOAD_DIR / req.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found or expired.")

    companies_data = read_all_companies(file_path, req.mappings)
    if not companies_data:
        raise HTTPException(status_code=400, detail="No companies found in uploaded file.")

    # Create Job record
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
    await db.flush()

    # Create Company records preserving all original data
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

    await db.commit()
    await db.refresh(new_job)

    # Launch background orchestrator
    orchestrator = ResearchOrchestrator(new_job.id, AsyncSessionLocal)
    task = asyncio.create_task(orchestrator.run())
    ACTIVE_JOBS[new_job.id] = {
        "orchestrator": orchestrator,
        "task": task
    }

    return new_job

@router.get("/{job_id}", response_model=JobOut)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    pct = 0.0
    if job.total_companies > 0:
        pct = round((job.processed_companies / job.total_companies) * 100, 1)
    
    # Add computed progress
    res = JobOut.model_validate(job)
    res.progress_percentage = pct
    return res

@router.post("/{job_id}/control", response_model=JobOut)
async def control_job(job_id: str, req: JobControlRequest, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
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
            # Re-launch
            orchestrator = ResearchOrchestrator(job_id, AsyncSessionLocal)
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
        # Reset failed companies to Unverified
        res = await db.execute(select(Company).where(Company.job_id == job_id, Company.overall_verification_status == "Failed"))
        failed_comps = res.scalars().all()
        for c in failed_comps:
            c.overall_verification_status = "Unverified"
        await db.commit()

        # Re-launch if not running
        if not active_entry or active_entry["task"].done():
            orchestrator = ResearchOrchestrator(job_id, AsyncSessionLocal)
            task = asyncio.create_task(orchestrator.run())
            ACTIVE_JOBS[job_id] = {"orchestrator": orchestrator, "task": task}
        job.status = "processing"
        job.current_stage = "Retrying failed companies"

    await db.commit()
    await db.refresh(job)
    return job

@router.get("", response_model=list[JobOut])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Job).order_by(desc(Job.created_at)).limit(20))
    jobs = res.scalars().all()
    out = []
    for j in jobs:
        pct = round((j.processed_companies / j.total_companies) * 100, 1) if j.total_companies > 0 else 0.0
        m = JobOut.model_validate(j)
        m.progress_percentage = pct
        out.append(m)
    return out
