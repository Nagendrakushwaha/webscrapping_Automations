from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Job, Company, Evidence, ManualReview
from ..core.excel_exporter import export_job_to_excel, export_job_to_csv

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/{job_id}/excel")
async def download_excel_export(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generates and downloads the full 4-sheet formatted Excel workbook for a research job.
    """
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    comp_res = await db.execute(select(Company).where(Company.job_id == job_id))
    companies = comp_res.scalars().all()

    ev_res = await db.execute(
        select(Evidence).join(Company, Evidence.company_id == Company.id).where(Company.job_id == job_id)
    )
    evidences = ev_res.scalars().all()

    rev_res = await db.execute(
        select(ManualReview).join(Company, ManualReview.company_id == Company.id).where(Company.job_id == job_id)
    )
    reviews = rev_res.scalars().all()

    file_path = export_job_to_excel(job, companies, evidences, reviews)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/{job_id}/csv")
async def download_csv_export(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generates and downloads the enriched leads CSV export for a research job.
    """
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    comp_res = await db.execute(select(Company).where(Company.job_id == job_id))
    companies = comp_res.scalars().all()

    file_path = export_job_to_csv(job, companies)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv"
    )
