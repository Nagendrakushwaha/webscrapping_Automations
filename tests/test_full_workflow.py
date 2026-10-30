import sys
import asyncio
from pathlib import Path
import openpyxl

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, SyncSessionLocal
from backend.app.models import Job, Company, Evidence, ManualReview
from backend.app.core.excel_parser import parse_and_preview, read_all_companies
from backend.app.core.excel_exporter import export_job_to_excel, export_job_to_csv
from backend.app.engine.query_generator import QueryGenerator
from backend.app.engine.verifier import DataVerifier
from backend.app.engine.orchestrator import ResearchOrchestrator

def test_excel_parsing():
    print("\n--- 1. Testing Excel Parsing & Column Mapping ---")
    sample_file = Path("sample_data/roofing_leads_sample.xlsx")
    assert sample_file.exists(), "Sample file does not exist!"

    preview = parse_and_preview(sample_file, sample_file.name)
    print(f"Total Rows: {preview['total_rows']}")
    print(f"Detected Headers: {preview['headers']}")
    print(f"Detected Mappings: {preview['detected_mappings']}")

    # Check that all original 8 columns are mapped
    expected_cols = ["id", "name", "trades", "city", "state", "phone", "webssite url", "claimed"]
    for col in expected_cols:
        assert col in preview["detected_mappings"], f"Missing mapping for {col}"

    companies = read_all_companies(sample_file, preview["detected_mappings"])
    assert len(companies) == 5, f"Expected 5 companies, got {len(companies)}"
    print(f"Successfully read {len(companies)} companies with preserved raw JSON!")
    return companies, preview["detected_mappings"]

def test_query_generator():
    print("\n--- 2. Testing AI Query Generator ---")
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
        print(f"  Field [{field_cat}]: {q_list[:2]}")
    assert "owner" in queries and len(queries["owner"]) > 0
    assert "personal_linkedin" in queries and len(queries["personal_linkedin"]) > 0
    print("AI Query Generator test PASSED!")

def test_email_verifier():
    print("\n--- 3. Testing Email Syntax & MX Verifier ---")
    status, reason = DataVerifier.verify_email_syntax_and_mx("contact@google.com")
    print(f"  Valid test (contact@google.com): {status} -> {reason}")
    assert status in ["Valid", "Unknown"]

    bad_status, bad_reason = DataVerifier.verify_email_syntax_and_mx("invalid-email-format")
    print(f"  Invalid format test: {bad_status} -> {bad_reason}")
    assert bad_status == "Invalid"
    print("Email Verifier test PASSED!")

async def test_end_to_end_research(companies_data, mappings):
    print("\n--- 4. Testing End-to-End Research Orchestration & DB Persistence ---")
    init_db()

    # Create test Job
    with SyncSessionLocal() as session:
        job = Job(
            filename="roofing_leads_sample.xlsx",
            total_companies=len(companies_data),
            status="pending"
        )
        session.add(job)
        session.flush()

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
        job_id = job.id

    print(f"Created Job {job_id} with {len(companies_data)} leads in SQLite.")

    # Run orchestrator on first 1 lead to verify live extraction without excessive wait
    orchestrator = ResearchOrchestrator(job_id)
    async with orchestrator.session_factory() as session:
        await orchestrator.load_configured_adapters(session)
        from sqlalchemy import select
        res = await session.execute(select(Company).where(Company.job_id == job_id).limit(1))
        test_batch = res.scalars().all()
        for comp in test_batch:
            print(f"  Executing research on: {comp.original_name} ({comp.original_website})...")
            await orchestrator._execute_company_research(comp, session)
        await orchestrator._refresh_job_statistics(session)

    # Verify results in DB
    with SyncSessionLocal() as session:
        refreshed_job = session.get(Job, job_id)
        comps = session.query(Company).where(Company.job_id == job_id).all()
        evidences = session.query(Evidence).join(Company).where(Company.job_id == job_id).all()
        reviews = session.query(ManualReview).join(Company).where(Company.job_id == job_id).all()

        print(f"  Job processed: {refreshed_job.processed_companies}/{refreshed_job.total_companies}")
        print(f"  Evidences collected: {len(evidences)}")
        for c in comps[:2]:
            print(f"    Company: {c.official_name}")
            print(f"      - Website Status: {c.website_status}")
            print(f"      - Business Email: {c.business_email} ({c.business_email_status})")
            print(f"      - Business Phone: {c.business_phone} ({c.business_phone_status})")
            print(f"      - Owner: {c.owner_name} ({c.owner_status})")
            print(f"      - Confidence Score: {c.overall_confidence_score}%")
            print(f"      - Overall Verification: {c.overall_verification_status}")

        print("\n--- 5. Testing Multi-Sheet Excel Export ---")
        excel_path = export_job_to_excel(refreshed_job, comps, evidences, reviews)
        assert excel_path.exists(), f"Excel file {excel_path} was not created!"
        print(f"  Created Excel workbook at: {excel_path}")

        # Validate sheets
        wb = openpyxl.load_workbook(excel_path)
        sheet_names = wb.sheetnames
        print(f"  Worksheets found: {sheet_names}")
        assert "Enriched Leads" in sheet_names
        assert "Research Evidence" in sheet_names
        assert "Manual Review" in sheet_names
        assert "Research Summary" in sheet_names

        # Check Sheet 1 headers: original columns first
        ws1 = wb["Enriched Leads"]
        row1_vals = [cell.value for cell in ws1[1]]
        assert row1_vals[:8] == ["id", "name", "trades", "city", "state", "phone", "webssite url", "claimed"], \
            "Original columns order violated in Sheet 1!"
        print("  Sheet 1 preserves all 8 original columns as the first 8 columns! PASSED.")

        # Test CSV export
        csv_path = export_job_to_csv(refreshed_job, comps)
        assert csv_path.exists()
        print(f"  Created CSV export at: {csv_path}")

    print("\n✅ ALL WORKFLOW TESTS PASSED SUCCESSFULLY!")

def main():
    comps, mappings = test_excel_parsing()
    test_query_generator()
    test_email_verifier()
    asyncio.run(test_end_to_end_research(comps, mappings))

if __name__ == "__main__":
    main()
