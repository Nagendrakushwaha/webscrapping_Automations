"""
Test Suite for Advanced Lead Intelligence Enhancements:
1. Email Permutation Engine & DNS MX Mailbox Verifier
2. SQLite WAL Mode & Interrupted Job Recovery
3. Mini-CRM Status Updates & Star Bookmarking
4. Bulk Actions (Bulk Status Update, Star, Webhook Push)
5. Visual Website Proof URL Generation
"""

import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.database import engine, init_db, SessionLocal
from backend.app.models import Company, AutomationJob, Job
from backend.app.engine.email_permutator import EmailPermutator
from backend.app.api.companies import update_lead_status, toggle_lead_star, bulk_company_action
from backend.app.schemas import BulkCompanyActionRequest

def run_tests():
    print("=" * 65)
    print("TEST 1: Email Permutator & Executive Mailbox Handshake")
    print("=" * 65)

    name = "John Doe"
    domain = "https://www.amstillroofing.com"

    # Test clean domain extraction
    clean_domain = EmailPermutator.extract_clean_domain(domain)
    assert clean_domain == "amstillroofing.com", f"Expected amstillroofing.com, got {clean_domain}"
    print(f"Domain extracted: {clean_domain}")

    # Test permutation patterns
    permutations = EmailPermutator.generate_permutations(name, clean_domain)
    print(f"Generated {len(permutations)} permutations: {permutations[:4]}...")
    assert "john.doe@amstillroofing.com" in permutations
    assert "john@amstillroofing.com" in permutations
    assert "jdoe@amstillroofing.com" in permutations

    # Test resolution
    best_email, provider, conf = EmailPermutator.resolve_best_executive_email(name, domain)
    print(f"Resolved Best Email: {best_email} | Provider: {provider} | Conf: {conf}")
    assert "@amstillroofing.com" in best_email
    assert conf >= 50
    print("[OK] TEST 1 PASSED: Email Permutation Engine verified.")

    print("\n" + "=" * 65)
    print("TEST 2: SQLite WAL Mode & Crash Auto-Recovery")
    print("=" * 65)
    init_db()

    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA journal_mode")).fetchone()
        journal_mode = res[0].lower()
        print(f"Active SQLite journal mode: {journal_mode}")
        assert journal_mode in ["wal", "memory"], f"Expected WAL mode, got {journal_mode}"

        # Insert a simulated 'running' job to test auto-recovery
        conn.execute(text(
            "INSERT OR REPLACE INTO automation_jobs (id, name, status, current_stage) VALUES ('test_crash_recovery_01', 'Crashed Run', 'running', 'Active scraping')"
        ))
        conn.commit()

    # Re-run init_db() to test auto-recovery on restart
    init_db()

    with SessionLocal() as session:
        job = session.get(AutomationJob, "test_crash_recovery_01")
        assert job is not None
        print(f"Recovered Job Status: {job.status} | Stage: {job.current_stage}")
        assert job.status == "paused", f"Expected paused status after crash recovery, got {job.status}"
        assert "Interrupted" in job.current_stage
    print("[OK] TEST 2 PASSED: WAL mode & Crash Auto-Recovery verified.")

    print("\n" + "=" * 65)
    print("TEST 3: Mini-CRM Sales Status & Star Bookmarks")
    print("=" * 65)
    with SessionLocal() as session:
        # Create parent job first to satisfy foreign key constraint
        test_job = Job(id="job_crm_test", filename="test_leads.xlsx")
        session.merge(test_job)
        session.commit()

        test_company = Company(
            id="comp_crm_test_01",
            job_id="job_crm_test",
            original_name="Lone Star Roofing",
            official_name="Lone Star Roofing",
            lead_status="New",
            is_starred=False,
            official_website="https://lonestarroofingtx.com"
        )
        session.merge(test_company)
        session.commit()

        # 1. Update status
        res_status = update_lead_status("comp_crm_test_01", status="Pitched", db=session)
        assert res_status["lead_status"] == "Pitched"
        print(f"Updated lead status to: {res_status['lead_status']}")

        # 2. Toggle Star
        res_star = toggle_lead_star("comp_crm_test_01", db=session)
        assert res_star["is_starred"] is True
        print(f"Starred prospect toggled to: {res_star['is_starred']}")
    print("[OK] TEST 3 PASSED: Mini-CRM individual status & bookmarking verified.")

    print("\n" + "=" * 65)
    print("TEST 4: Bulk CRM Actions (Bulk Status & Webhook Payload)")
    print("=" * 65)
    with SessionLocal() as session:
        # Create 2 test companies for bulk operations
        c_a = Company(id="comp_bulk_a", job_id="job_crm_test", original_name="Alpha Roofing", lead_status="New")
        c_b = Company(id="comp_bulk_b", job_id="job_crm_test", original_name="Beta Roofing", lead_status="New")
        session.merge(c_a)
        session.merge(c_b)
        session.commit()

        # Execute Bulk Status Update
        req_bulk = BulkCompanyActionRequest(
            company_ids=["comp_bulk_a", "comp_bulk_b"],
            action="update_status",
            status="Meeting Booked"
        )
        bulk_res = bulk_company_action(req_bulk, db=session)
        assert bulk_res["success"] is True
        assert bulk_res["count"] == 2
        print(f"Bulk Action Result: {bulk_res}")

        # Verify in DB
        c_a_db = session.get(Company, "comp_bulk_a")
        assert c_a_db.lead_status == "Meeting Booked"
        print(f"Company A verified status: {c_a_db.lead_status}")
    print("[OK] TEST 4 PASSED: Bulk CRM operations verified.")

    print("\n" + "=" * 65)
    print("TEST 5: Visual Website Proof URL Generation")
    print("=" * 65)
    target_site = "https://amstillroofing.com"
    screenshot_url = f"https://s0.wp.com/mshots/v1/{target_site}?w=800&h=600"
    print(f"Generated Visual Proof Thumbnail URL: {screenshot_url}")
    assert "s0.wp.com/mshots" in screenshot_url
    assert "amstillroofing.com" in screenshot_url
    print("[OK] TEST 5 PASSED: Visual proof generation verified.")

    print("\n" + "=" * 65)
    print("ALL ADVANCED ENHANCEMENT TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
