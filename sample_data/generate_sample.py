import pandas as pd
from pathlib import Path

DATA = [
    {
        "id": "ROOF-001",
        "name": "Kanga Roof",
        "trades": "Roofing, Gutters, Siding",
        "city": "Round Rock",
        "state": "TX",
        "phone": "(512) 388-7663",
        "webssite url": "https://kangaroof.com",
        "claimed": "Yes"
    },
    {
        "id": "ROOF-002",
        "name": "Austin Roofing and Construction",
        "trades": "Residential & Commercial Roofing",
        "city": "Austin",
        "state": "TX",
        "phone": "(512) 629-4949",
        "webssite url": "https://austinroofingandconstruction.com",
        "claimed": "Yes"
    },
    {
        "id": "ROOF-003",
        "name": "Kidd Roofing",
        "trades": "Roofing Contractor",
        "city": "Austin",
        "state": "TX",
        "phone": "(512) 671-7791",
        "webssite url": "https://kiddroof.com",
        "claimed": "Yes"
    },
    {
        "id": "ROOF-004",
        "name": "Ja-Mar Roofing & Sheet Metal",
        "trades": "Roofing, Sheet Metal",
        "city": "Buda",
        "state": "TX",
        "phone": "(512) 441-8437",
        "webssite url": "https://jamarroofing.com",
        "claimed": "Yes"
    },
    {
        "id": "ROOF-005",
        "name": "Wilson Roofing Co",
        "trades": "Roofing Installation & Repair",
        "city": "Austin",
        "state": "TX",
        "phone": "(512) 263-3157",
        "webssite url": "https://wilsonroofing.com",
        "claimed": "No"
    }
]

df = pd.DataFrame(DATA)
out_dir = Path("sample_data")
out_dir.mkdir(exist_ok=True)

excel_path = out_dir / "roofing_leads_sample.xlsx"
csv_path = out_dir / "roofing_leads_sample.csv"

df.to_excel(excel_path, index=False)
df.to_csv(csv_path, index=False)
print(f"Generated {excel_path} and {csv_path}")
