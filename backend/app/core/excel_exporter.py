import json
from datetime import datetime
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from ..config import EXPORT_DIR
from ..models import Job, Company, Evidence, ManualReview

HEADER_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
DATA_FONT = Font(name="Calibri", size=10)
LINK_FONT = Font(name="Calibri", size=10, color="2563EB", underline="single")
THIN_BORDER = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)

def style_header_row(ws, col_count: int):
    ws.freeze_panes = "A2"
    for col_idx in range(1, col_count + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.auto_filter.ref = ws.dimensions

def auto_fit_columns(ws, min_width=12, max_width=45):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or '')
            if cell.hyperlink:
                val = str(cell.hyperlink.target or val)
            lines = val.split("\n")
            for line in lines:
                if len(line) > max_len:
                    max_len = len(line)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)

def export_job_to_excel(job: Job, companies: list[Company], evidences: list[Evidence], reviews: list[ManualReview]) -> Path:
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # ==========================================
    # SHEET 1: Enriched Leads
    # ==========================================
    ws_leads = wb.create_sheet(title="Enriched Leads")
    
    headers_sheet1 = [
        # Original Columns (Preserved 1st)
        "id", "name", "trades", "city", "state", "phone", "webssite url", "claimed",
        # Business Details
        "Official Business Name", "Business Category", "Business Description", "Full Business Address", 
        "ZIP Code", "Country", "Year Established", "Company Size", "Official Website", "Website Status",
        # Mandatory Decision-Maker Fields (1-4)
        "Owner Name", "Owner Job Title", "CEO Name", "CEO Job Title", 
        "Founder Name", "Founder Job Title", "Co-Founder Name", "Co-Founder Job Title", 
        "Primary Decision Maker", "Primary Decision Maker Title",
        # Mandatory Contact Fields (5-8)
        "Business Email", "Additional Business Emails", "Business Phone", "Additional Business Phone", 
        "Personal Professional Email", "Public Professional Phone", "Email Verification Status",
        # Mandatory Social Fields (9-12)
        "Personal LinkedIn", "Business LinkedIn", "Business Instagram", "Business Facebook",
        # Research Information
        "Owner Verification Status", "CEO Verification Status", "Founder Verification Status", "Co-Founder Verification Status",
        "Business Email Status", "Business Phone Status", "Personal Email Status", "Personal Phone Status", 
        "Personal LinkedIn Status", "Business LinkedIn Status", "Instagram Status", "Facebook Status", 
        "Overall Confidence Score", "Overall Verification Status", "Missing Fields", "Last Checked", "Research Notes"
    ]
    ws_leads.append(headers_sheet1)

    for comp in companies:
        add_emails = ", ".join(json.loads(comp.additional_business_emails or "[]"))
        add_phones = ", ".join(json.loads(comp.additional_business_phones or "[]"))
        missing = ", ".join(json.loads(comp.missing_fields or "[]"))
        last_chk = comp.last_checked.strftime("%Y-%m-%d %H:%M:%S") if comp.last_checked else ""

        row = [
            comp.original_id, comp.original_name, comp.original_trades, comp.original_city,
            comp.original_state, comp.original_phone, comp.original_website, comp.original_claimed,
            comp.official_name or comp.original_name, comp.business_category or comp.trades,
            comp.business_description, comp.address, comp.zip_code, comp.country,
            comp.year_established, comp.company_size, comp.official_website, comp.website_status,
            comp.owner_name, comp.owner_title, comp.ceo_name, comp.ceo_title,
            comp.founder_name, comp.founder_title, comp.cofounder_name, comp.cofounder_title,
            comp.primary_decision_maker, comp.primary_decision_maker_title,
            comp.business_email, add_emails, comp.business_phone, add_phones,
            comp.personal_email, comp.personal_phone, comp.email_verification_status,
            comp.personal_linkedin, comp.business_linkedin, comp.business_instagram, comp.business_facebook,
            comp.owner_status, comp.ceo_status, comp.founder_status, comp.cofounder_status,
            comp.business_email_status, comp.business_phone_status, comp.personal_email_status, comp.personal_phone_status,
            comp.personal_linkedin_status, comp.business_linkedin_status, comp.business_instagram_status, comp.business_facebook_status,
            comp.overall_confidence_score, comp.overall_verification_status, missing, last_chk, comp.research_notes
        ]
        ws_leads.append(row)
        curr_row = ws_leads.max_row
        
        # Apply formatting and links
        for c_idx in range(1, len(row) + 1):
            cell = ws_leads.cell(row=curr_row, column=c_idx)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            val = str(cell.value or "")
            if val.startswith("http://") or val.startswith("https://"):
                cell.hyperlink = val
                cell.font = LINK_FONT

    style_header_row(ws_leads, len(headers_sheet1))
    auto_fit_columns(ws_leads)

    # ==========================================
    # SHEET 2: Research Evidence
    # ==========================================
    ws_evidence = wb.create_sheet(title="Research Evidence")
    headers_sheet2 = [
        "Business ID", "Business Name", "Field Name", "Discovered Value", 
        "Source Name", "Source URL", "Discovery Date", "Last Checked", 
        "Verification Status", "Confidence Score", "Supporting Evidence"
    ]
    ws_evidence.append(headers_sheet2)

    comp_lookup = {c.id: c for c in companies}
    for ev in evidences:
        comp = comp_lookup.get(ev.company_id)
        b_id = comp.original_id if comp else ""
        b_name = comp.original_name if comp else ""
        disc_date = ev.discovery_date.strftime("%Y-%m-%d %H:%M:%S") if ev.discovery_date else ""
        last_date = ev.last_checked.strftime("%Y-%m-%d %H:%M:%S") if ev.last_checked else ""

        ws_evidence.append([
            b_id, b_name, ev.field_name, ev.discovered_value,
            ev.source_name, ev.source_url, disc_date, last_date,
            ev.verification_status, ev.confidence_score, ev.notes
        ])
        curr_row = ws_evidence.max_row
        for c_idx in range(1, len(headers_sheet2) + 1):
            cell = ws_evidence.cell(row=curr_row, column=c_idx)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx == 6 and str(cell.value or "").startswith("http"):
                cell.hyperlink = str(cell.value)
                cell.font = LINK_FONT

    style_header_row(ws_evidence, len(headers_sheet2))
    auto_fit_columns(ws_evidence)

    # ==========================================
    # SHEET 3: Manual Review
    # ==========================================
    ws_review = wb.create_sheet(title="Manual Review")
    headers_sheet3 = [
        "Business ID", "Business Name", "Field", "Conflicting Values", 
        "Source URLs", "Reason for Review", "Suggested Action", "Review Status"
    ]
    ws_review.append(headers_sheet3)

    for rev in reviews:
        comp = comp_lookup.get(rev.company_id)
        b_id = comp.original_id if comp else ""
        b_name = comp.original_name if comp else ""
        conf_vals = " | ".join(json.loads(rev.conflicting_values or "[]"))
        urls = " | ".join(json.loads(rev.source_urls or "[]"))

        ws_review.append([
            b_id, b_name, rev.field_name, conf_vals, urls,
            rev.reason, rev.suggested_action, rev.review_status
        ])
        curr_row = ws_review.max_row
        for c_idx in range(1, len(headers_sheet3) + 1):
            cell = ws_review.cell(row=curr_row, column=c_idx)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER

    style_header_row(ws_review, len(headers_sheet3))
    auto_fit_columns(ws_review)

    # ==========================================
    # SHEET 4: Research Summary
    # ==========================================
    ws_summary = wb.create_sheet(title="Research Summary")
    ws_summary.append(["AI LEAD INTELLIGENCE - RESEARCH SUMMARY REPORT"])
    ws_summary.append(["Generated by Tex Web Solutions Pvt. Ltd.", f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"])
    ws_summary.append([])
    
    summary_data = [
        ["Job ID", job.id],
        ["Filename", job.filename],
        ["Total Businesses Uploaded", job.total_companies],
        ["Total Businesses Processed", job.processed_companies],
        ["Successfully Enriched", job.enriched_count],
        ["Fully Verified", job.fully_verified_count],
        ["Partially Verified", job.partially_verified_count],
        ["Unverified", job.unverified_count],
        ["Not Found / Empty", job.not_found_count],
        ["Failed / Errored", job.failed_count],
        ["Requires Manual Review", job.manual_review_count],
        ["Job Status", job.status.upper()],
        ["Job Started", job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else ""],
        ["Job Last Updated", job.updated_at.strftime("%Y-%m-%d %H:%M:%S") if job.updated_at else ""],
    ]
    for row in summary_data:
        ws_summary.append(row)

    # Title styling
    ws_summary.cell(row=1, column=1).font = Font(name="Calibri", size=14, bold=True, color="1E293B")
    ws_summary.cell(row=2, column=1).font = Font(name="Calibri", size=10, italic=True, color="64748B")
    for r in range(4, 4 + len(summary_data)):
        ws_summary.cell(row=r, column=1).font = Font(name="Calibri", size=11, bold=True)
        ws_summary.cell(row=r, column=2).font = Font(name="Calibri", size=11)
        ws_summary.cell(row=r, column=1).border = THIN_BORDER
        ws_summary.cell(row=r, column=2).border = THIN_BORDER

    auto_fit_columns(ws_summary)

    # Save to export directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_fn = Path(job.filename).stem.replace(" ", "_")
    export_filename = f"Enriched_{clean_fn}_{timestamp}.xlsx"
    export_path = EXPORT_DIR / export_filename
    wb.save(export_path)

    return export_path

def export_job_to_csv(job: Job, companies: list[Company]) -> Path:
    """
    Exports Sheet 1 data directly to CSV.
    """
    data = []
    for comp in companies:
        add_emails = ", ".join(json.loads(comp.additional_business_emails or "[]"))
        add_phones = ", ".join(json.loads(comp.additional_business_phones or "[]"))
        missing = ", ".join(json.loads(comp.missing_fields or "[]"))
        last_chk = comp.last_checked.strftime("%Y-%m-%d %H:%M:%S") if comp.last_checked else ""

        row = {
            "id": comp.original_id,
            "name": comp.original_name,
            "trades": comp.original_trades,
            "city": comp.original_city,
            "state": comp.original_state,
            "phone": comp.original_phone,
            "webssite url": comp.original_website,
            "claimed": comp.original_claimed,
            "Official Business Name": comp.official_name or comp.original_name,
            "Business Category": comp.business_category or comp.trades,
            "Business Description": comp.business_description,
            "Full Business Address": comp.address,
            "ZIP Code": comp.zip_code,
            "Country": comp.country,
            "Year Established": comp.year_established,
            "Company Size": comp.company_size,
            "Official Website": comp.official_website,
            "Website Status": comp.website_status,
            "Owner Name": comp.owner_name,
            "Owner Job Title": comp.owner_title,
            "CEO Name": comp.ceo_name,
            "CEO Job Title": comp.ceo_title,
            "Founder Name": comp.founder_name,
            "Founder Job Title": comp.founder_title,
            "Co-Founder Name": comp.cofounder_name,
            "Co-Founder Job Title": comp.cofounder_title,
            "Primary Decision Maker": comp.primary_decision_maker,
            "Primary Decision Maker Title": comp.primary_decision_maker_title,
            "Business Email": comp.business_email,
            "Additional Business Emails": add_emails,
            "Business Phone": comp.business_phone,
            "Additional Business Phone": add_phones,
            "Personal Professional Email": comp.personal_email,
            "Public Professional Phone": comp.personal_phone,
            "Email Verification Status": comp.email_verification_status,
            "Personal LinkedIn": comp.personal_linkedin,
            "Business LinkedIn": comp.business_linkedin,
            "Business Instagram": comp.business_instagram,
            "Business Facebook": comp.business_facebook,
            "Owner Verification Status": comp.owner_status,
            "CEO Verification Status": comp.ceo_status,
            "Founder Verification Status": comp.founder_status,
            "Co-Founder Verification Status": comp.cofounder_status,
            "Business Email Status": comp.business_email_status,
            "Business Phone Status": comp.business_phone_status,
            "Personal Email Status": comp.personal_email_status,
            "Personal Phone Status": comp.personal_phone_status,
            "Personal LinkedIn Status": comp.personal_linkedin_status,
            "Business LinkedIn Status": comp.business_linkedin_status,
            "Instagram Status": comp.business_instagram_status,
            "Facebook Status": comp.business_facebook_status,
            "Overall Confidence Score": comp.overall_confidence_score,
            "Overall Verification Status": comp.overall_verification_status,
            "Missing Fields": missing,
            "Last Checked": last_chk,
            "Research Notes": comp.research_notes
        }
        data.append(row)

    df = pd.DataFrame(data)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_fn = Path(job.filename).stem.replace(" ", "_")
    export_filename = f"Enriched_{clean_fn}_{timestamp}.csv"
    export_path = EXPORT_DIR / export_filename
    df.to_csv(export_path, index=False, encoding="utf-8-sig")
    return export_path

