"""
Test Suite for Upload & File Preview Endpoints:
1. Verify route registration on FastAPI app (no 405 on POST /api/jobs/preview or /api/jobs/upload).
2. Verify upload_file_and_preview function with Excel & CSV (headers, original_headers, detected mappings).
3. Verify upload_file_and_start_job function with form mapping.
4. Verify start_research_job JSON endpoint for backward compatibility.
"""

import sys
import os
import io
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi import UploadFile, BackgroundTasks
from backend.app.main import app
from backend.app.database import init_db, SessionLocal
from backend.app.models import Job, Company
from backend.app.api.jobs import (
    upload_file_and_preview,
    upload_file_and_start_job,
    start_research_job
)
from backend.app.schemas import ColumnMappingRequest

def test_routes():
    print("=" * 65)
    print("TEST 1: Verify FastAPI Route Registration")
    print("=" * 65)

    from backend.app.api.jobs import router as jobs_router

    registered = []
    for route in jobs_router.routes:
        methods = getattr(route, "methods", set())
        path = getattr(route, "path", "")
        registered.append((path, methods))

    print(f"Registered /api/jobs routes ({len(registered)}):")
    for path, methods in registered:
        print(f"  {sorted(list(methods))} -> {path}")

    # Check POST /api/jobs/preview
    preview_routes = [r for r in registered if r[0] == "/api/jobs/preview" and "POST" in r[1]]
    assert len(preview_routes) > 0, "POST /api/jobs/preview NOT found in FastAPI routes!"

    # Check POST /api/jobs/upload
    upload_routes = [r for r in registered if r[0] == "/api/jobs/upload" and "POST" in r[1]]
    assert len(upload_routes) > 0, "POST /api/jobs/upload NOT found in FastAPI routes!"

    # Check POST /api/jobs/upload-preview
    up_prev_routes = [r for r in registered if r[0] == "/api/jobs/upload-preview" and "POST" in r[1]]
    assert len(up_prev_routes) > 0, "POST /api/jobs/upload-preview NOT found in FastAPI routes!"

    # Check POST /api/jobs/start-research
    start_routes = [r for r in registered if r[0] == "/api/jobs/start-research" and "POST" in r[1]]
    assert len(start_routes) > 0, "POST /api/jobs/start-research NOT found in FastAPI routes!"

    print("[OK] TEST 1 PASSED: All upload and preview routes correctly registered.")

def test_upload_and_preview():
    print("\n" + "=" * 65)
    print("TEST 2: Upload File & Preview Parsing")
    print("=" * 65)

    sample_path = Path("sample_data/roofing_leads_sample.xlsx")
    assert sample_path.exists(), f"Sample file {sample_path} not found"

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    upload_file = UploadFile(
        file=io.BytesIO(file_bytes),
        filename="roofing_leads_sample.xlsx"
    )

    preview = upload_file_and_preview(upload_file)
    print(f"Preview filename: {preview['filename']}")
    print(f"Total rows: {preview['total_rows']}")
    print(f"Headers: {preview['headers']}")
    print(f"Original headers: {preview['original_headers']}")
    print(f"Detected mappings: {preview['detected_mappings']}")

    assert preview["total_rows"] == 5
    assert len(preview["preview_rows"]) == 5
    assert "headers" in preview and len(preview["headers"]) > 0
    assert "original_headers" in preview and len(preview["original_headers"]) > 0
    assert "name" in preview["detected_mappings"]
    assert "website_url" in preview["detected_mappings"] or "webssite url" in preview["detected_mappings"]
    print("[OK] TEST 2 PASSED: Upload preview parsed accurately.")
    return preview

def test_upload_and_start_job(preview):
    print("\n" + "=" * 65)
    print("TEST 3: Upload File & Start Job (Frontend Flow)")
    print("=" * 65)

    init_db()
    db = SessionLocal()

    sample_path = Path("sample_data/roofing_leads_sample.xlsx")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    upload_file = UploadFile(
        file=io.BytesIO(file_bytes),
        filename="roofing_leads_sample.xlsx"
    )

    column_mapping = json.dumps({
        "id": "id",
        "name": "name",
        "trades": "trades",
        "city": "city",
        "state": "state",
        "phone": "phone",
        "website_url": "webssite url",
        "claimed": "claimed"
    })

    bg_tasks = BackgroundTasks()

    job_out = upload_file_and_start_job(
        background_tasks=bg_tasks,
        file=upload_file,
        column_mapping=column_mapping,
        db=db
    )

    print(f"Created Job ID: {job_out.id}")
    print(f"Total companies in Job: {job_out.total_companies}")
    print(f"Job Status: {job_out.status}")

    assert job_out.total_companies == 5
    assert job_out.status == "pending"

    # Verify Company records created in DB
    companies = db.query(Company).filter(Company.job_id == job_out.id).all()
    print(f"Companies inserted into DB: {len(companies)}")
    assert len(companies) == 5

    first = companies[0]
    print(f"Lead 1: Name='{first.original_name}', Website='{first.original_website}', City='{first.city}'")
    assert first.original_name != ""
    assert first.lead_status == "New"

    db.close()
    print("[OK] TEST 3 PASSED: Upload and start job creates Job and Company entities.")

def test_start_research_backward_compatibility(preview):
    print("\n" + "=" * 65)
    print("TEST 4: Backward Compatibility start_research_job")
    print("=" * 65)

    init_db()
    db = SessionLocal()

    req = ColumnMappingRequest(
        file_id=preview["file_id"],
        mappings=preview["detected_mappings"],
        settings={"industry": "Roofing", "country": "USA"}
    )
    bg_tasks = BackgroundTasks()
    job_out = start_research_job(req, bg_tasks, db)

    print(f"Start Research Job ID: {job_out.id}")
    assert job_out.total_companies == 5

    db.close()
    print("[OK] TEST 4 PASSED: start_research_job backward compatibility confirmed.")

if __name__ == "__main__":
    test_routes()
    preview = test_upload_and_preview()
    test_upload_and_start_job(preview)
    test_start_research_backward_compatibility(preview)
    print("\n" + "=" * 65)
    print("ALL UPLOAD FIX TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 65)
