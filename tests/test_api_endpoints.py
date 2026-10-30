import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.main import app
from backend.app.database import init_db

def test_api():
    print("\n--- Testing FastAPI Endpoints with TestClient ---", flush=True)
    init_db()
    client = TestClient(app)

    # 1. Health Check
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"Health Check: {health_data}", flush=True)
    assert health_data["app"] == "AI LEAD INTELLIGENCE"
    assert health_data["company"] == "Tex Web Solutions Pvt. Ltd."

    # 2. Settings Endpoint
    settings_resp = client.get("/api/settings")
    assert settings_resp.status_code == 200
    providers = settings_resp.json()
    print(f"Supported API Providers ({len(providers)}): {[p['provider_name'] for p in providers]}", flush=True)
    assert len(providers) >= 8

    # 3. Upload & Preview Endpoint
    sample_file = Path("sample_data/roofing_leads_sample.xlsx")
    with open(sample_file, "rb") as f:
        upload_resp = client.post(
            "/api/jobs/upload-preview",
            files={"file": (sample_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert upload_resp.status_code == 200, f"Upload preview failed: {upload_resp.text}"
    preview_data = upload_resp.json()
    print(f"Upload Preview Succeeded! File ID: {preview_data['file_id']}, Rows: {preview_data['total_rows']}", flush=True)
    assert preview_data["total_rows"] == 5
    assert "webssite url" in preview_data["detected_mappings"]

    # 4. Start Research Job Endpoint
    start_payload = {
        "file_id": preview_data["file_id"],
        "mappings": preview_data["detected_mappings"],
        "settings": {
            "industry": "Roofing",
            "country": "USA",
            "concurrency": 2
        }
    }
    start_resp = client.post("/api/jobs/start-research", json=start_payload)
    assert start_resp.status_code == 200, f"Start job failed: {start_resp.text}"
    job_data = start_resp.json()
    job_id = job_data["id"]
    print(f"Research Job Started: ID = {job_id}, Total Leads = {job_data['total_companies']}", flush=True)
    assert job_data["total_companies"] == 5

    # 5. Get Job Status Endpoint
    job_status_resp = client.get(f"/api/jobs/{job_id}")
    assert job_status_resp.status_code == 200
    print(f"Job Status Checked: {job_status_resp.json()['status']}", flush=True)

    # 6. List Companies for Job Endpoint
    comps_resp = client.get(f"/api/companies/job/{job_id}")
    assert comps_resp.status_code == 200
    comps_data = comps_resp.json()
    print(f"Companies listed: {len(comps_data['items'])} of {comps_data['total']}", flush=True)
    assert comps_data["total"] == 5
    first_comp_id = comps_data["items"][0]["id"]

    # 7. Get Company Detail Endpoint
    comp_detail_resp = client.get(f"/api/companies/{first_comp_id}")
    assert comp_detail_resp.status_code == 200
    detail_data = comp_detail_resp.json()
    print(f"Company Detail: {detail_data['official_name']} - Original ID: {detail_data['original_id']}", flush=True)
    assert detail_data["original_name"] != ""

    # 8. Export Excel Endpoint
    excel_resp = client.get(f"/api/export/{job_id}/excel")
    assert excel_resp.status_code == 200
    assert len(excel_resp.content) > 1000, "Excel export content too small!"
    print(f"Excel Export verified: {len(excel_resp.content)} bytes received.", flush=True)

    # 9. Export CSV Endpoint
    csv_resp = client.get(f"/api/export/{job_id}/csv")
    assert csv_resp.status_code == 200
    assert "Official Business Name" in csv_resp.text
    print(f"CSV Export verified: {len(csv_resp.text.splitlines())} lines received.", flush=True)

    # 10. Root SPA Endpoint
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    print("Root SPA HTML successfully served!", flush=True)

    print("\n[SUCCESS] ALL FASTAPI ENDPOINTS TESTED AND VERIFIED!", flush=True)

if __name__ == "__main__":
    test_api()

