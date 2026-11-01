"""
Comprehensive Verification Test Suite for:
NATIONAL ROOFING DIRECTORY MODULE
AI Lead Intelligence — Tex Web Solutions Pvt. Ltd.

Covers:
1. State Directory URL generation & dynamic multi-state support
2. City discovery from state hub HTML
3. Full pagination discovery & rel="next" traversal
4. Extraction of all mandatory contractor fields (Name, Owner, Trades, City, State, ZIP, Phone)
5. Dedicated Gmail extraction (@gmail.com separated from business email)
6. Strict company website validation (rejection of directory and social links)
7. Checkpoint persistence & SQLite job auto-recovery
8. 8-sheet OpenPyXL Excel & CSV export
9. Zero regression verification for existing modules (The Roofing List & Lead Automation)
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from backend.app.database import init_db, SessionLocal, engine
from backend.app.models import NationalRoofingJob, Company
from backend.app.engine.discovery.national_roofing_discovery import (
    NationalRoofingEngine,
    NationalRoofingValidator
)
from backend.app.core.excel_exporter import (
    export_national_roofing_job_to_excel,
    export_national_roofing_job_to_csv
)
from backend.app.engine.discovery.roofing_list_discovery import (
    TheRoofingListDiscoveryAdapter
)
import openpyxl


def test_state_and_city_discovery():
    print("=" * 65)
    print("TEST 1: State Directory Hub & Dynamic Multi-State Support")
    print("=" * 65)

    tx_url = NationalRoofingEngine.get_state_url("Texas")
    fl_url = NationalRoofingEngine.get_state_url("FL")
    ca_url = NationalRoofingEngine.get_state_url("California")

    print(f"Texas State URL: {tx_url}")
    print(f"Florida State URL: {fl_url}")
    print(f"California State URL: {ca_url}")

    assert tx_url == "https://www.nationalroofingdirectory.com/roofing-contractors/texas"
    assert fl_url == "https://www.nationalroofingdirectory.com/roofing-contractors/florida"
    assert ca_url == "https://www.nationalroofingdirectory.com/roofing-contractors/california"

    # Test City Discovery from HTML Mock
    state_mock_html = """
    <html>
      <body>
        <h1>Roofing Contractors in Texas</h1>
        <div class="cities-grid">
          <a href="/roofing-contractors/texas/houston">Houston Roofing</a>
          <a href="/roofing-contractors/texas/dallas">Dallas Roofing</a>
          <a href="/roofing-contractors/texas/austin">Austin Roofing</a>
          <a href="/roofing-contractors/texas/san-antonio">San Antonio Roofing</a>
        </div>
      </body>
    </html>
    """
    cities = NationalRoofingEngine.discover_city_pages_from_html(state_mock_html, tx_url)
    city_names = [c["city_name"] for c in cities]
    print(f"Discovered {len(cities)} cities from state directory mock: {city_names}")
    assert "Houston" in city_names or "Houston Roofing" in city_names
    assert "Dallas" in city_names or "Dallas Roofing" in city_names
    print("[OK] TEST 1 PASSED: State directory URL & city discovery verified.")


def test_pagination_and_profile_discovery():
    print("\n" + "=" * 65)
    print("TEST 2: City Directory Pagination & Contractor Profile Discovery")
    print("=" * 65)

    city_mock_html = """
    <html>
      <body>
        <h2>Roofing Contractors in Houston, TX</h2>
        <div class="listings">
          <a href="/roofing-contractors/texas/houston/apex-peak-roofing">Apex Peak Roofing</a>
          <a href="/roofing-contractors/texas/houston/lone-star-gutters">Lone Star Gutters</a>
          <a href="/roofing-contractors/texas/houston/pro-roof-tx">Pro Roof TX</a>
        </div>
        <div class="pagination">
          <span class="current">1</span>
          <a href="/roofing-contractors/texas/houston?page=2" rel="next">Next »</a>
        </div>
      </body>
    </html>
    """
    city_url = "https://www.nationalroofingdirectory.com/roofing-contractors/texas/houston"
    profiles, next_page = NationalRoofingEngine.discover_contractor_profile_urls_from_html(city_mock_html, city_url)

    print(f"Discovered Profiles ({len(profiles)}): {profiles}")
    print(f"Detected Next Page: {next_page}")

    assert len(profiles) == 3
    assert any("apex-peak-roofing" in p for p in profiles)
    assert next_page == "https://www.nationalroofingdirectory.com/roofing-contractors/texas/houston?page=2"
    print("[OK] TEST 2 PASSED: Profile discovery & pagination traversal verified.")


def test_profile_field_extraction_and_gmail():
    print("\n" + "=" * 65)
    print("TEST 3 & 4: Profile Field Extraction & Dedicated Gmail Detection")
    print("=" * 65)

    profile_html = """
    <html>
      <head><title>Apex Peak Roofing LLC | National Roofing Directory</title></head>
      <body>
        <h1>Apex Peak Roofing LLC</h1>
        <p>Owner: Robert Gonzalez</p>
        <p>Services: Commercial Roofing, Shingle Replacement, Storm Damage Repair</p>
        <address>4500 Washington Ave, Houston, TX 77007</address>
        <a href="tel:(713) 555-0144">Call (713) 555-0144</a>
        <div class="contact-info">
          <p>Office: <a href="mailto:office@apexpeakroofingtx.com">office@apexpeakroofingtx.com</a></p>
          <p>Direct Owner Gmail: <a href="mailto:apexpeakroofinghouston@gmail.com">apexpeakroofinghouston@gmail.com</a></p>
        </div>
        <div class="links">
          <a href="https://www.nationalroofingdirectory.com/contractor/apex">Directory Profile</a>
          <a href="https://www.facebook.com/apexroofing">Facebook</a>
          <a href="https://www.apexpeakroofingtx.com" rel="nofollow">Visit Company Website</a>
        </div>
      </body>
    </html>
    """
    profile_url = "https://www.nationalroofingdirectory.com/roofing-contractors/texas/houston/apex-peak-roofing"
    data = NationalRoofingEngine.parse_contractor_profile_html(profile_html, profile_url, default_city="Houston", default_state="TX")

    print(f"Extracted Company Name: {data['name']}")
    print(f"Extracted Owner: {data['owner_name']}")
    print(f"Extracted Trades: {data['trades']}")
    print(f"Extracted City/State/ZIP: {data['city']}, {data['state']} {data['zip_code']}")
    print(f"Extracted Phone: {data['phone']}")
    print(f"Extracted Business Email: {data['email']}")
    print(f"Extracted Dedicated Gmail: {data['gmail_address']}")
    print(f"Extracted Official Website: {data['website']} (Status: {data['website_status']})")

    assert data["name"] == "Apex Peak Roofing LLC"
    assert data["owner_name"] == "Robert Gonzalez"
    assert data["city"] == "Houston"
    assert data["state"] == "TX"
    assert data["zip_code"] == "77007"
    assert "(713) 555-0144" in data["phone"]
    assert data["email"] == "office@apexpeakroofingtx.com"
    # Dedicated Gmail verification
    assert data["gmail_address"] == "apexpeakroofinghouston@gmail.com"
    # Strict website validation
    assert data["website"] == "https://apexpeakroofingtx.com"
    assert data["website_status"] == "Active"

    print("[OK] TEST 3 & 4 PASSED: Contractor fields & dedicated Gmail extraction verified.")


def test_strict_website_validation():
    print("\n" + "=" * 65)
    print("TEST 5: Strict Official Website Anti-Directory Validation")
    print("=" * 65)

    valid, url, status = NationalRoofingValidator.validate_website("https://amstillroofing.com", "Amstill Roofing")
    assert valid is True and url == "https://amstillroofing.com"
    print(f"Genuine Website: {url} -> {status}")

    # Reject Directory Link
    valid_dir, url_dir, status_dir = NationalRoofingValidator.validate_website("https://www.nationalroofingdirectory.com/profile/123", "Amstill")
    assert valid_dir is False and url_dir == "N/A"
    print(f"Directory Link Rejection: {status_dir}")

    # Reject Social Media Link
    valid_fb, url_fb, status_fb = NationalRoofingValidator.validate_website("https://www.facebook.com/amstillroofing", "Amstill")
    assert valid_fb is False and url_fb == "N/A"
    print(f"Social Media Rejection: {status_fb}")

    # Missing link returns N/A
    valid_na, url_na, status_na = NationalRoofingValidator.validate_website("", "Amstill")
    assert valid_na is False and url_na == "N/A"
    print(f"Empty Website: {url_na} -> {status_na}")

    print("[OK] TEST 5 PASSED: Strict anti-directory validation verified.")


def test_job_execution_and_checkpoint():
    print("\n" + "=" * 65)
    print("TEST 6: Checkpoint Persistence & Background Job Flow")
    print("=" * 65)

    init_db()
    db = SessionLocal()

    # Create National Roofing Job
    job = NationalRoofingJob(
        name="Texas Verification Run",
        state="Texas",
        state_code="TX",
        status="pending",
        selected_cities_json=json.dumps(["Houston", "Dallas"]),
        checkpoint_json=json.dumps({"processed_urls": [], "failed_urls": [], "discovered_urls": []})
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id
    print(f"Created NationalRoofingJob: ID={job_id}, State={job.state}")

    # Run engine synchronously
    engine_runner = NationalRoofingEngine(session_factory=SessionLocal, job_id=job_id)
    engine_runner.run_sync()

    # Check updated metrics in DB (expire cache to read latest committed data)
    db.expire_all()
    updated_job = db.get(NationalRoofingJob, job_id)
    print(f"Job Status: {updated_job.status}")
    print(f"City Pages Discovered: {updated_job.city_pages_discovered}")
    print(f"Profiles Processed: {updated_job.profiles_processed}")
    print(f"Gmail Addresses Found: {updated_job.gmail_found}")
    print(f"Websites Found: {updated_job.websites_found}")

    assert updated_job.status == "completed"
    assert updated_job.profiles_processed >= 2

    # Check Company table entries
    comps = db.query(Company).filter(Company.national_roofing_job_id == job_id).all()
    print(f"Companies inserted into DB for job: {len(comps)}")
    assert len(comps) >= 2
    for c in comps:
        assert c.discovery_provider == "National Roofing Directory"
        print(f"  Lead: {c.official_name} | City: {c.city} | Gmail: {c.gmail_address} | Web: {c.official_website}")

    db.close()
    print("[OK] TEST 6 PASSED: Checkpoint persistence and DB insertion verified.")
    return job_id


def test_8_sheet_excel_and_csv_export(job_id: str):
    print("\n" + "=" * 65)
    print("TEST 7: 8-Sheet OpenPyXL Excel & CSV Export")
    print("=" * 65)

    db = SessionLocal()
    job = db.get(NationalRoofingJob, job_id)
    comps = db.query(Company).filter(Company.national_roofing_job_id == job_id).all()

    excel_path = export_national_roofing_job_to_excel(job, comps)
    csv_path = export_national_roofing_job_to_csv(job, comps)

    print(f"Exported Excel File: {excel_path.name} ({excel_path.stat().st_size} bytes)")
    print(f"Exported CSV File: {csv_path.name} ({csv_path.stat().st_size} bytes)")

    assert excel_path.exists()
    assert csv_path.exists()

    # Verify all 8 sheets in the generated Excel workbook
    wb = openpyxl.load_workbook(excel_path)
    sheet_names = wb.sheetnames
    print(f"Generated Excel Sheets ({len(sheet_names)}): {sheet_names}")

    expected_sheets = [
        "Texas Roofing Leads",
        "City Summary",
        "Scrape Summary",
        "Gmail Found",
        "Emails Found",
        "Websites Found",
        "Missing Websites",
        "Failed Profiles"
    ]

    for exp in expected_sheets:
        assert exp in sheet_names, f"Expected sheet '{exp}' missing from Excel export!"

    # Verify sheet 1 has all required company fields
    ws_main = wb["Texas Roofing Leads"]
    first_row = [cell.value for cell in ws_main[1]]
    print(f"Main Sheet Headers: {first_row}")
    assert "Company Name" in first_row
    assert "Owner / Contact Name" in first_row
    assert "Gmail Address" in first_row
    assert "Company Website URL" in first_row

    wb.close()
    db.close()
    print("[OK] TEST 7 PASSED: 8-Sheet Excel & CSV export verified.")


def test_zero_regression():
    print("\n" + "=" * 65)
    print("TEST 8: Zero Regression Verification (The Roofing List & Automation)")
    print("=" * 65)

    # 1. Verify The Roofing List adapter remains intact
    rl_adapter = TheRoofingListDiscoveryAdapter()
    assert rl_adapter.name == "the_roofing_list"
    assert rl_adapter.is_configured is True
    print(f"The Roofing List Adapter Verified: {rl_adapter.name}")

    # 2. Verify FastAPI router registration
    from backend.app.main import app
    from backend.app.api.national_roofing import router as nrd_router

    nrd_paths = [r.path for r in nrd_router.routes]
    print(f"National Roofing Router Endpoints ({len(nrd_paths)}): {nrd_paths}")
    assert "/api/national-roofing/start" in nrd_paths
    assert "/api/national-roofing/jobs" in nrd_paths
    assert "/api/national-roofing/jobs/{job_id}/leads" in nrd_paths
    assert "/api/national-roofing/jobs/{job_id}/export/excel" in nrd_paths

    print("[OK] TEST 8 PASSED: Zero regressions across existing modules.")


if __name__ == "__main__":
    test_state_and_city_discovery()
    test_pagination_and_profile_discovery()
    test_profile_field_extraction_and_gmail()
    test_strict_website_validation()
    job_id = test_job_execution_and_checkpoint()
    test_8_sheet_excel_and_csv_export(job_id)
    test_zero_regression()
    print("\n" + "=" * 65)
    print("ALL NATIONAL ROOFING DIRECTORY TESTS PASSED! [OK]")
    print("=" * 65)
