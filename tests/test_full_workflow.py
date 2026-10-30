import sys
import asyncio
from pathlib import Path
import openpyxl

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, SessionLocal
from backend.app.models import Job, Company, Evidence, ManualReview
from backend.app.core.excel_parser import parse_and_preview, read_all_companies
from backend.app.core.excel_exporter import export_job_to_excel, export_job_to_csv
from backend.app.engine.query_generator import QueryGenerator
from backend.app.engine.verifier import DataVerifier
from backend.app.engine.orchestrator import ResearchOrchestrator

def test_excel_parsing():
    print("\n--- 1. Testing Excel Parsing & Column Mapping ---", flush=True)
    sample_file = Path("sample_data/roofing_leads_sample.xlsx")
    assert sample_file.exists(), "Sample file does not exist!"

    preview = parse_and_preview(sample_file, sample_file.name)
    print(f"Total Rows: {preview['total_rows']}", flush=True)
    print(f"Detected Headers: {preview['headers']}", flush=True)
    print(f"Detected Mappings: {preview['detected_mappings']}", flush=True)

    expected_cols = ["id", "name", "trades", "city", "state", "phone", "webssite url", "claimed"]
    for col in expected_cols:
        assert col in preview["detected_mappings"], f"Missing mapping for {col}"

    companies = read_all_companies(sample_file, preview["detected_mappings"])
    assert len(companies) == 5, f"Expected 5 companies, got {len(companies)}"
    print(f"Successfully read {len(companies)} companies with preserved raw JSON!", flush=True)
    return companies, preview["detected_mappings"]

def test_query_generator():
    print("\n--- 2. Testing AI Query Generator ---", flush=True)
    gen = QueryGenerator()
    test_comp = {
        "name": "Kanga Roof LLC",
        "city": "Round Rock",
        "state": "TX",
        "website url": "https://kangaroof.com",
        "phone": "(512) 388-7663"
    }
    queries = gen.generate_all_queries(test_comp)
    for field_cat, q_list in queries.items():
        print(f"  Field [{field_cat}]: {q_list[:2]}", flush=True)
    assert "owner" in queries and len(queries["owner"]) > 0
    assert "personal_linkedin" in queries and len(queries["personal_linkedin"]) > 0
    print("AI Query Generator test PASSED!", flush=True)

def test_email_verifier():
    print("\n--- 3. Testing Email Syntax & MX Verifier ---", flush=True)
    status, reason = DataVerifier.verify_email_syntax_and_mx("contact@google.com")
    print(f"  Valid test (contact@google.com): {status} -> {reason}", flush=True)
    assert status in ["Valid", "Unknown"]

    bad_status, bad_reason = DataVerifier.verify_email_syntax_and_mx("invalid-email-format")
    print(f"  Invalid format test: {bad_status} -> {bad_reason}", flush=True)
    assert bad_status == "Invalid"
    print("Email Verifier test PASSED!", flush=True)

def test_end_to_end_research(companies_data, mappings):
    print("\n--- 4. Testing End-to-End Research Orchestration & DB Persistence ---", flush=True)
    init_db()

    job_id = None
    with SessionLocal() as session:
        job = Job(
            filename="roofing_leads_sample.xlsx",
            total_companies=len(companies_data),
            status="pending"
        )
        session.add(job)
        session.flush()
        job_id = job.id

        for c in companies_data:
            comp = Company(
                job_id=job.id,
                original_id=c["original_id"],
                original_name=c["original_name"],
                original_trades=c["original_trades"],
                original_city=c["original_city"],
                original_state=c["original_state"],
                original_phone=c["original_phone"],
                original_website=c["original_website"],
                original_claimed=c["original_claimed"],
                raw_data_json=c["raw_data_json"],
                official_name=c["original_name"],
                official_website=c["original_website"],
                overall_verification_status="Unverified"
            )
            session.add(comp)
        session.commit()

    print(f"Created Job {job_id} with {len(companies_data)} leads in SQLite.", flush=True)

    orchestrator = ResearchOrchestrator(job_id)
    
    # Mock crawler response to simulate rich website data
    def mock_crawl_sync(url):
        return {
            "official_website": url,
            "domain": "kangaroof.com",
            "website_status": "Active",
            "title": "Kanga Roof - Premier Austin Roofing Contractors",
            "description": "Family-owned roofing contractor in Round Rock and Austin since 1992.",
            "address": "123 Main St, Round Rock, TX 78664",
            "zip_code": "78664",
            "year_established": "1992",
            "emails": ["info@kangaroof.com", "service@kangaroof.com"],
            "phones": ["(512) 388-7663"],
            "personal_linkedin": "https://www.linkedin.com/in/kangaruler",
            "business_linkedin": "https://www.linkedin.com/company/kanga-roof",
            "business_instagram": "https://www.instagram.com/kangaroof",
            "business_facebook": "https://www.facebook.com/kangaroof",
            "decision_makers": [
                {"name": "Scott R. Simpson", "title": "Owner & Founder", "role_type": "Owner", "source_url": f"{url}/about"}
            ],
            "pages_found": {"about": f"{url}/about", "contact": f"{url}/contact"},
            "evidence": [
                {
                    "field_name": "Owner",
                    "discovered_value": "Scott R. Simpson",
                    "source_name": "Website Crawler",
                    "source_url": f"{url}/about",
                    "confidence_score": 95,
                    "verification_status": "Verified",
                    "notes": "Listed on leadership page"
                }
            ]
        }
    
    orchestrator.website_adapter.crawl_and_extract_sync = mock_crawl_sync

    with SessionLocal() as session:
        comp = session.query(Company).filter(Company.job_id == job_id).first()
        print(f"  Executing research on: {comp.original_name} ({comp.original_website})...", flush=True)
        orchestrator.execute_company_research_sync(comp, session)
        orchestrator._refresh_job_statistics(session)

    # Verify results in DB
    with SessionLocal() as session:
        refreshed_job = session.get(Job, job_id)
        comps = session.query(Company).filter(Company.job_id == job_id).all()
        evidences = session.query(Evidence).join(Company).filter(Company.job_id == job_id).all()
        reviews = session.query(ManualReview).join(Company).filter(Company.job_id == job_id).all()

        print(f"  Job processed: {refreshed_job.processed_companies}/{refreshed_job.total_companies}", flush=True)
        print(f"  Evidences collected: {len(evidences)}", flush=True)
        for c in comps[:1]:
            print(f"    Company: {c.official_name}", flush=True)
            print(f"      - Website Status: {c.website_status}", flush=True)
            print(f"      - Business Email: {c.business_email} ({c.business_email_status})", flush=True)
            print(f"      - Business Phone: {c.business_phone} ({c.business_phone_status})", flush=True)
            print(f"      - Owner: {c.owner_name} ({c.owner_status})", flush=True)
            print(f"      - Primary Decision Maker: {c.primary_decision_maker} ({c.primary_decision_maker_title})", flush=True)
            print(f"      - Personal LinkedIn: {c.personal_linkedin}", flush=True)
            print(f"      - Business LinkedIn: {c.business_linkedin}", flush=True)
            print(f"      - Business Instagram: {c.business_instagram}", flush=True)
            print(f"      - Business Facebook: {c.business_facebook}", flush=True)
            print(f"      - Confidence Score: {c.overall_confidence_score}%", flush=True)
            print(f"      - Overall Verification: {c.overall_verification_status}", flush=True)

        print("\n--- 5. Testing Multi-Sheet Excel Export ---", flush=True)
        excel_path = export_job_to_excel(refreshed_job, comps, evidences, reviews)
        assert excel_path.exists(), f"Excel file {excel_path} was not created!"
        print(f"  Created Excel workbook at: {excel_path}", flush=True)

        # Validate sheets
        wb = openpyxl.load_workbook(excel_path)
        sheet_names = wb.sheetnames
        print(f"  Worksheets found: {sheet_names}", flush=True)
        assert "Enriched Leads" in sheet_names
        assert "Research Evidence" in sheet_names
        assert "Manual Review" in sheet_names
        assert "Research Summary" in sheet_names

        # Check Sheet 1 headers: original columns first
        ws1 = wb["Enriched Leads"]
        row1_vals = [cell.value for cell in ws1[1]]
        assert row1_vals[:8] == ["id", "name", "trades", "city", "state", "phone", "webssite url", "claimed"], \
            "Original columns order violated in Sheet 1!"
        print("  Sheet 1 preserves all 8 original columns as the first 8 columns! PASSED.", flush=True)

        # Test CSV export
        csv_path = export_job_to_csv(refreshed_job, comps)
        assert csv_path.exists()
        print(f"  Created CSV export at: {csv_path}", flush=True)

    print("\n[SUCCESS] ALL WORKFLOW TESTS PASSED SUCCESSFULLY!", flush=True)

def main():
    comps, mappings = test_excel_parsing()
    test_query_generator()
    test_email_verifier()
    test_end_to_end_research(comps, mappings)

if __name__ == "__main__":
    main()
