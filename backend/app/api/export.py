from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, Company, Evidence, ManualReview, AutomationJob
from ..core.excel_exporter import (
    export_job_to_excel, export_job_to_csv,
    export_automation_to_excel, export_automation_to_csv
)

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/{job_id}/excel")
def download_excel_export(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    companies = db.query(Company).filter(Company.job_id == job_id).all()
    evidences = db.query(Evidence).join(Company, Evidence.company_id == Company.id).filter(Company.job_id == job_id).all()
    reviews = db.query(ManualReview).join(Company, ManualReview.company_id == Company.id).filter(Company.job_id == job_id).all()

    file_path = export_job_to_excel(job, companies, evidences, reviews)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/{job_id}/csv")
def download_csv_export(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    companies = db.query(Company).filter(Company.job_id == job_id).all()
    file_path = export_job_to_csv(job, companies)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv"
    )

@router.get("/automation/{automation_id}/excel")
def download_automation_excel_export(automation_id: str, db: Session = Depends(get_db)):
    auto_job = db.get(AutomationJob, automation_id)
    if not auto_job:
        raise HTTPException(status_code=404, detail="Automation job not found.")

    companies = db.query(Company).filter(Company.automation_id == automation_id).all()
    file_path = export_automation_to_excel(auto_job, companies)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/automation/{automation_id}/csv")
def download_automation_csv_export(automation_id: str, db: Session = Depends(get_db)):
    auto_job = db.get(AutomationJob, automation_id)
    if not auto_job:
        raise HTTPException(status_code=404, detail="Automation job not found.")

    companies = db.query(Company).filter(Company.automation_id == automation_id).all()
    file_path = export_automation_to_csv(auto_job, companies)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv"
    )
