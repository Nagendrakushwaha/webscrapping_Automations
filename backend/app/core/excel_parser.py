import json
import uuid
from pathlib import Path
from typing import Any
import pandas as pd
from ..config import UPLOAD_DIR

STANDARD_COLUMNS = {
    "id": ["id", "business_id", "company_id", "lead_id", "#", "row_id"],
    "name": ["name", "company_name", "business_name", "company", "business"],
    "trades": ["trades", "trade", "industry", "services", "category", "business_category"],
    "city": ["city", "town", "municipality"],
    "state": ["state", "province", "st", "region"],
    "phone": ["phone", "telephone", "phone_number", "tel", "mobile", "contact_number"],
    "webssite url": ["webssite url", "website url", "website", "url", "domain", "company_website", "web"],
    "claimed": ["claimed", "is_claimed", "claim_status", "verified_listing"]
}

def detect_column_mappings(file_headers: list[str]) -> dict[str, str]:
    """
    Automatically maps standard field names to detected columns in the uploaded file.
    """
    mappings: dict[str, str] = {}
    normalized_headers = {h.strip().lower().replace("_", " "): h for h in file_headers}

    for std_field, candidates in STANDARD_COLUMNS.items():
        found = False
        # 1. Exact match on standard key
        if std_field in normalized_headers:
            mappings[std_field] = normalized_headers[std_field]
            continue
            
        # 2. Check candidate variations
        for cand in candidates:
            cand_norm = cand.lower().replace("_", " ")
            if cand_norm in normalized_headers:
                mappings[std_field] = normalized_headers[cand_norm]
                found = True
                break
        
        # 3. Substring match if not found
        if not found:
            for norm_h, original_h in normalized_headers.items():
                if std_field in norm_h or any(c in norm_h for c in candidates):
                    mappings[std_field] = original_h
                    break

    return mappings

def parse_and_preview(file_path: Path, filename: str) -> dict[str, Any]:
    """
    Parses an uploaded file, extracts metadata, preview rows, and checks for duplicates.
    """
    ext = file_path.suffix.lower()
    
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        except Exception:
            df = pd.read_csv(file_path, encoding="latin1", dtype=str, keep_default_na=False)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Please upload a CSV or XLSX file.")

    headers = [str(col).strip() for col in df.columns]
    df.columns = headers
    total_rows = len(df)

    # Detect duplicates (based on name + phone or name + city)
    dup_subset = []
    for col in headers:
        col_lower = col.lower()
        if "name" in col_lower or "phone" in col_lower:
            dup_subset.append(col)
    
    duplicate_count = 0
    if dup_subset:
        duplicate_count = int(df.duplicated(subset=dup_subset, keep="first").sum())

    # Get preview of first 10 rows
    preview_df = df.head(10).fillna("")
    preview_rows = preview_df.to_dict(orient="records")

    detected_mappings = detect_column_mappings(headers)

    return {
        "filename": filename,
        "total_rows": total_rows,
        "headers": headers,
        "preview_rows": preview_rows,
        "detected_mappings": detected_mappings,
        "duplicate_count": duplicate_count
    }

def read_all_companies(file_path: Path, mappings: dict[str, str]) -> list[dict[str, Any]]:
    """
    Reads all companies from file, extracting mapped columns while keeping full raw row JSON.
    """
    ext = file_path.suffix.lower()
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        except Exception:
            df = pd.read_csv(file_path, encoding="latin1", dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)

    df.columns = [str(col).strip() for col in df.columns]
    
    companies = []
    for idx, row in df.iterrows():
        raw_dict = {k: ("" if pd.isna(v) else str(v).strip()) for k, v in row.items()}
        
        # Extract according to mappings
        orig_id = raw_dict.get(mappings.get("id", ""), "").strip() or f"lead_{idx+1}"
        orig_name = raw_dict.get(mappings.get("name", ""), "").strip()
        orig_trades = raw_dict.get(mappings.get("trades", ""), "").strip()
        orig_city = raw_dict.get(mappings.get("city", ""), "").strip()
        orig_state = raw_dict.get(mappings.get("state", ""), "").strip()
        orig_phone = raw_dict.get(mappings.get("phone", ""), "").strip()
        orig_website = raw_dict.get(mappings.get("webssite url", ""), "").strip()
        orig_claimed = raw_dict.get(mappings.get("claimed", ""), "").strip()

        companies.append({
            "original_id": orig_id,
            "original_name": orig_name,
            "original_trades": orig_trades,
            "original_city": orig_city,
            "original_state": orig_state,
            "original_phone": orig_phone,
            "original_website": orig_website,
            "original_claimed": orig_claimed,
            "raw_data_json": json.dumps(raw_dict, ensure_ascii=False)
        })

    return companies
