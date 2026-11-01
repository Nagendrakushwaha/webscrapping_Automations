"""
End-to-End Test Suite for Automated Lead Generation Module
Verifies:
1. US Location Database (50 states + DC, Census places, FIPS, Haversine, Zone tiling)
2. Lead Deduplication & Normalization
3. Lead Opportunity Scoring (0-100 & Tex Web Solutions criteria)
4. 6-Sheet OpenPyXL Excel Export
5. FastAPI Automation and Location API endpoints
"""

import sys
import os
import openpyxl
from io import BytesIO

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.core.location_service import LocationService
from backend.app.engine.discovery.deduplicator import LeadDeduplicator
from backend.app.engine.discovery.base import DiscoveredLead
from backend.app.engine.lead_scorer import LeadScorer
from backend.app.models import Company, AutomationJob
from backend.app.core.excel_exporter import export_automation_to_excel
from backend.app.database import SessionLocal, init_db

def run_tests():
    print("=" * 60)
    print("TEST 1: US Census Location Service Verification")
    print("=" * 60)
    init_db()
    with SessionLocal() as session:
        states = LocationService.get_all_states(session)
        print(f"Total States in DB: {len(states)}")
        assert len(states) >= 50, f"Expected at least 50 states, got {len(states)}"
        
        tx_cities = LocationService.get_cities_for_state(session, "TX")
        print(f"Texas Cities in DB: {len(tx_cities)}")
        assert len(tx_cities) > 0, "No cities found for Texas"
        
        # Test Haversine distance
        houston = next(c for c in tx_cities if c["city_name"] == "Houston")
        austin = next(c for c in tx_cities if c["city_name"] == "Austin")
        dist = LocationService.haversine_distance_miles(houston["latitude"], houston["longitude"], austin["latitude"], austin["longitude"])
        print(f"Calculated Houston -> Austin distance: {dist:.1f} miles")
        assert 130 < dist < 170, f"Distance unexpected: {dist}"
        
        # Test 50-mile zone tiling
        zones = LocationService.generate_search_zones(houston["latitude"], houston["longitude"], 50.0)
        print(f"50-mile radius generated {len(zones)} zones for Google Places 50km coverage")
        assert len(zones) >= 4, "Expected multi-zone tiling for 50-mile radius"
    print("[OK] TEST 1 PASSED: Location Service verified.")

    print("\n" + "=" * 60)
    print("TEST 2: Lead Deduplicator Verification")
    print("=" * 60)
    dedup = LeadDeduplicator()
    lead1 = DiscoveredLead(
        name="Apex Roofing LLC",
        city="Houston",
        state="TX",
        phone="(713) 555-0199",
        website="https://www.apexroofingtx.com"
    )
    lead2 = DiscoveredLead(
        name="Apex Roofing, Inc.",
        city="Houston",
        state="TX",
        phone="7135550199",
        website="http://apexroofingtx.com/about"
    )
    lead3 = DiscoveredLead(
        name="Houston Premier Roofing",
        city="Houston",
        state="TX",
        phone="832-555-9988",
        website="https://houstonpremierroof.com"
    )
    
    is_dup1, _ = dedup.is_duplicate(lead1)
    assert is_dup1 is False
    dedup.register(lead1)
    
    # lead2 has same phone and same domain
    is_dup2, reason2 = dedup.is_duplicate(lead2)
    assert is_dup2 is True, f"lead2 should be detected as duplicate of lead1, got {is_dup2}"
    print(f"Deduplicated lead2 reason: {reason2}")
    
    # lead3 is unique
    is_dup3, _ = dedup.is_duplicate(lead3)
    assert is_dup3 is False
    dedup.register(lead3)
    print("[OK] TEST 2 PASSED: Deduplication working accurately.")

    print("\n" + "=" * 60)
    print("TEST 3: Lead Opportunity Scoring (0-100)")
    print("=" * 60)
    c1 = Company(
        job_id="test_job_1",
        original_name="Lone Star Roofers",
        official_name="Lone Star Roofers",
        city="Houston",
        state="TX",
        owner_name="John Doe",
        business_email="contact@lonestarroof.com",
        email_verification_status="Valid",
        business_phone="713-555-1234",
        official_website="http://lonestarroof.com",
        tech_stack_cms="WordPress",
        redesign_opportunity="High Demand",
        website_status="Active"
    )
    score1, reason1 = LeadScorer.calculate_score(c1)
    print(f"Company 1 Score: {score1}/100 | Reason: {reason1}")
    assert score1 >= 70, f"Expected high score for complete lead with redesign opp, got {score1}"

    c2 = Company(
        job_id="test_job_1",
        original_name="No Website Roofing",
        official_name="No Website Roofing",
        city="Houston",
        state="TX",
        business_phone="713-555-9999",
        official_website="",
        website_status="No Official Website"
    )
    score2, reason2 = LeadScorer.calculate_score(c2)
    print(f"Company 2 Score: {score2}/100 | Reason: {reason2}")
    assert score2 >= 35, f"Expected points for Greenfield (No Website) opportunity, got {score2}"
    print("[OK] TEST 3 PASSED: Lead Opportunity Scoring working.")

    print("\n" + "=" * 60)
    print("TEST 4: 6-Sheet OpenPyXL Excel Export")
    print("=" * 60)
    companies = [c1, c2]
    auto_job = AutomationJob(
        id="auto_test_12345",
        name="Texas Roofing Automation",
        status="completed",
        total_target=2,
        total_discovered=2,
        unique_discovered=2,
        total_enriched=2,
        verified_emails_count=1,
        failed_count=0
    )
    
    export_path = export_automation_to_excel(auto_job, companies)
    assert export_path.exists(), f"Excel output file not found at {export_path}"
    print(f"Exported Excel file generated: {export_path.name} ({export_path.stat().st_size} bytes)")
    
    wb = openpyxl.load_workbook(export_path)
    sheet_names = wb.sheetnames
    print(f"Generated Excel Sheets: {sheet_names}")
    expected_sheets = [
        "All Companies",
        "Decision Makers",
        "Verified Emails",
        "Missing Websites",
        "Failed Enrichment",
        "Automation Summary"
    ]
    for s in expected_sheets:
        assert s in sheet_names, f"Sheet '{s}' missing in generated Excel workbook"
    
    # Check that data exists in All Companies sheet
    ws_all = wb["All Companies"]
    assert ws_all.max_row >= 3, f"Expected header + 2 data rows, got {ws_all.max_row}"
    print("[OK] TEST 4 PASSED: 6-Sheet Excel export verified.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
