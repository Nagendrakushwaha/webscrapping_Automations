import json
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
from ..database import get_db
from ..models import Company
from ..schemas import CompanyOut, CompanyDetailOut, BulkCompanyActionRequest, WebhookPushResponse

router = APIRouter(prefix="/api/companies", tags=["Companies"])

@router.get("/job/{job_id}", response_model=dict)
def list_companies_for_job(
    job_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = None,
    status: Optional[str] = None,
    has_owner: Optional[bool] = None,
    has_email: Optional[bool] = None,
    has_linkedin: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Company).filter(Company.job_id == job_id)

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(or_(
            Company.original_name.ilike(search_term),
            Company.official_name.ilike(search_term),
            Company.city.ilike(search_term),
            Company.state.ilike(search_term),
            Company.owner_name.ilike(search_term),
            Company.business_email.ilike(search_term),
            Company.business_phone.ilike(search_term)
        ))

    if status and status != "All":
        query = query.filter(Company.overall_verification_status == status)

    if has_owner is True:
        query = query.filter(Company.owner_name != "")
    elif has_owner is False:
        query = query.filter(Company.owner_name == "")

    if has_email is True:
        query = query.filter(Company.business_email != "")
    elif has_email is False:
        query = query.filter(Company.business_email == "")

    if has_linkedin is True:
        query = query.filter(or_(Company.personal_linkedin != "", Company.business_linkedin != ""))

    total_count = query.count()
    offset = (page - 1) * limit
    companies = (
        query.order_by(desc(Company.overall_confidence_score), Company.created_at)
        .offset(offset)
        .limit(limit)
        .all()
    )

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
def get_company_detail(company_id: str, db: Session = Depends(get_db)):
    comp = (
        db.query(Company)
        .options(
            joinedload(Company.evidence),
            joinedload(Company.manual_reviews),
            joinedload(Company.decision_makers)
        )
        .filter(Company.id == company_id)
        .first()
    )
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found.")

    detail = CompanyDetailOut.model_validate(comp)
    detail.missing_fields = json.loads(comp.missing_fields or "[]")
    detail.additional_business_emails = json.loads(comp.additional_business_emails or "[]")
    detail.additional_business_phones = json.loads(comp.additional_business_phones or "[]")
    detail.sources_searched = json.loads(comp.sources_searched or "[]")

    for r in detail.manual_reviews:
        r.conflicting_values = json.loads(r.conflicting_values if isinstance(r.conflicting_values, str) else "[]")
        r.source_urls = json.loads(r.source_urls if isinstance(r.source_urls, str) else "[]")

    return detail

@router.patch("/{company_id}/status")
def update_lead_status(company_id: str, status: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Updates sales CRM status (New, Contacted, Pitched, Replied, Meeting Booked, Closed, Not Interested)."""
    comp = db.get(Company, company_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found")
    comp.lead_status = status
    db.commit()
    return {"success": True, "company_id": company_id, "lead_status": comp.lead_status}

@router.patch("/{company_id}/star")
def toggle_lead_star(company_id: str, is_starred: Optional[bool] = Body(None, embed=True), db: Session = Depends(get_db)):
    """Toggles starred / high priority prospect bookmark."""
    comp = db.get(Company, company_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found")
    if is_starred is None:
        comp.is_starred = not bool(comp.is_starred)
    else:
        comp.is_starred = bool(is_starred)
    db.commit()
    return {"success": True, "company_id": company_id, "is_starred": comp.is_starred}

@router.post("/bulk-action")
def bulk_company_action(req: BulkCompanyActionRequest, db: Session = Depends(get_db)):
    """
    Executes bulk actions across selected leads:
    - update_status: Bulk update sales pipeline status
    - star / unstar: Bulk bookmarking
    - delete: Remove selected records
    - webhook_push: Stream selected leads to Zapier / Make / n8n / CRM
    """
    if not req.company_ids:
        return {"success": False, "count": 0, "message": "No company IDs provided"}

    q = db.query(Company).filter(Company.id.in_(req.company_ids))
    companies = q.all()

    action = req.action.lower().strip()
    if action == "update_status" and req.status:
        for c in companies:
            c.lead_status = req.status
        db.commit()
        return {"success": True, "action": action, "count": len(companies), "status": req.status}

    elif action == "star":
        for c in companies:
            c.is_starred = True
        db.commit()
        return {"success": True, "action": action, "count": len(companies)}

    elif action == "unstar":
        for c in companies:
            c.is_starred = False
        db.commit()
        return {"success": True, "action": action, "count": len(companies)}

    elif action == "delete":
        count = len(companies)
        for c in companies:
            db.delete(c)
        db.commit()
        return {"success": True, "action": action, "count": count}

    elif action == "webhook_push":
        if not req.webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required for webhook_push action")
        
        leads_payload = []
        for c in companies:
            leads_payload.append({
                "id": c.id,
                "name": c.official_name or c.original_name,
                "industry": c.trades or c.original_trades,
                "city": c.city or c.original_city,
                "state": c.state or c.original_state,
                "phone": c.business_phone or c.original_phone,
                "website": c.official_website or c.original_website,
                "lead_score": c.lead_score,
                "lead_status": c.lead_status,
                "owner_name": c.owner_name,
                "ceo_name": c.ceo_name,
                "business_email": c.business_email,
                "personal_email": c.personal_email,
                "cms": c.tech_stack_cms,
                "redesign_opportunity": c.redesign_opportunity,
                "pitch": c.ai_personalized_pitch
            })

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(req.webhook_url, json={"source": "AI LEAD INTELLIGENCE", "total": len(leads_payload), "leads": leads_payload})
                return {
                    "success": resp.status_code in [200, 201, 202, 204],
                    "sent_count": len(leads_payload),
                    "status_code": resp.status_code,
                    "message": f"Successfully pushed {len(leads_payload)} leads to webhook."
                }
        except Exception as e:
            return {
                "success": False,
                "sent_count": 0,
                "message": f"Webhook delivery error: {str(e)}"
            }

    raise HTTPException(status_code=400, detail=f"Unsupported bulk action: {action}")

