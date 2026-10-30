import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import Company, Evidence, ManualReview, DecisionMakerRecord
from ..schemas import CompanyOut, CompanyDetailOut

router = APIRouter(prefix="/api/companies", tags=["Companies"])

@router.get("/job/{job_id}", response_model=dict)
async def list_companies_for_job(
    job_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = None,
    status: Optional[str] = None,
    has_owner: Optional[bool] = None,
    has_email: Optional[bool] = None,
    has_linkedin: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Searchable, sortable, filterable company results table endpoint.
    """
    filters = [Company.job_id == job_id]

    if q:
        search_term = f"%{q.strip()}%"
        filters.append(or_(
            Company.original_name.ilike(search_term),
            Company.official_name.ilike(search_term),
            Company.city.ilike(search_term),
            Company.state.ilike(search_term),
            Company.owner_name.ilike(search_term),
            Company.business_email.ilike(search_term),
            Company.business_phone.ilike(search_term)
        ))

    if status and status != "All":
        filters.append(Company.overall_verification_status == status)

    if has_owner is True:
        filters.append(Company.owner_name != "")
    elif has_owner is False:
        filters.append(Company.owner_name == "")

    if has_email is True:
        filters.append(Company.business_email != "")
    elif has_email is False:
        filters.append(Company.business_email == "")

    if has_linkedin is True:
        filters.append(or_(Company.personal_linkedin != "", Company.business_linkedin != ""))

    # Count query
    count_query = select(Company.id).where(and_(*filters))
    total_res = await db.execute(count_query)
    total_count = len(total_res.scalars().all())

    # Data query
    offset = (page - 1) * limit
    data_query = (
        select(Company)
        .where(and_(*filters))
        .order_by(desc(Company.overall_confidence_score), Company.created_at)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(data_query)
    companies = result.scalars().all()

    items = []
    for c in companies:
        m = CompanyOut.model_validate(c)
        m.missing_fields = json.loads(c.missing_fields or "[]")
        items.append(m)

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/{company_id}", response_model=CompanyDetailOut)
async def get_company_detail(company_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full details for a company, including full evidence ledger, conflicts, and decision makers.
    """
    stmt = (
        select(Company)
        .options(
            selectinload(Company.evidence),
            selectinload(Company.manual_reviews),
            selectinload(Company.decision_makers)
        )
        .where(Company.id == company_id)
    )
    res = await db.execute(stmt)
    comp = res.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found.")

    detail = CompanyDetailOut.model_validate(comp)
    detail.missing_fields = json.loads(comp.missing_fields or "[]")
    detail.additional_business_emails = json.loads(comp.additional_business_emails or "[]")
    detail.additional_business_phones = json.loads(comp.additional_business_phones or "[]")
    detail.sources_searched = json.loads(comp.sources_searched or "[]")

    # Map manual review JSON lists
    for r in detail.manual_reviews:
        r.conflicting_values = json.loads(r.conflicting_values if isinstance(r.conflicting_values, str) else "[]")
        r.source_urls = json.loads(r.source_urls if isinstance(r.source_urls, str) else "[]")

    return detail
