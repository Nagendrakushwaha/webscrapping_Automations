# AI LEAD INTELLIGENCE

**A Production-Ready Automated B2B Lead Research, Enrichment & Verification Application**  
*Built for:* **Tex Web Solutions Pvt. Ltd.**  
*Services:* Website Design | Website Development | Website Redesign | Web Applications | SEO | Digital Solutions  

---

## 🚀 Overview

**AI LEAD INTELLIGENCE** is a web application designed to automatically research, enrich, verify, and organize business leads from spreadsheets (XLSX and CSV). 

While initially targeted at **US Roofing Companies**, the application is fully modular and supports any trade, industry, city, state, and country.

### Key Capabilities
- **Original Data Protection**: Preserves all 8 original columns (`id`, `name`, `trades`, `city`, `state`, `phone`, `webssite url`, `claimed`) intact.
- **Mandatory 12 Fields**: Systematically attempts to discover, match, and verify all 12 key decision-maker, contact, and social data points for every single lead.
- **Multi-Source Research**: Integrates direct company website crawling, search APIs (Tavily, Google, Bing, Brave, DuckDuckGo), business registries, Google Places, and B2B databases (Apollo, Hunter).
- **Verification & Confidence Scoring**: Assigns an evidence-backed confidence score (0–100) and verification status to every discovered field. Performs real-time email MX record deliverability checks via DNS.
- **Multi-Sheet Formatted Excel Export**: Generates a professional 4-sheet formatted Excel workbook (`.xlsx`) with clickable links and data filters, plus CSV export.
- **Real-Time Job Controls**: Live progress bar, current company and research stage indicators, pause, resume, stop, and retry failed companies.

---

## 📋 The 12 Mandatory Search Fields

For every company, the research engine attempts all 12 fields:

1. **Owner**: Full name, confirmed company association, current job title.
2. **CEO**: Full name, current designation, confirmed association.
3. **Founder**: Full name, confirmed company association.
4. **Co-Founder**: Full name, confirmed company association.
5. **Business Email**: Official company, sales, or inquiries email.
6. **Business Phone**: Main company or office phone number.
7. **Personal Professional Email**: Published professional email of decision-maker (strictly public, zero guessing).
8. **Public Professional Phone**: Published direct line of decision-maker.
9. **Personal LinkedIn**: Verified public LinkedIn profile URL of the decision-maker.
10. **Business LinkedIn**: Official company LinkedIn page URL.
11. **Business Instagram**: Official verified company Instagram account.
12. **Business Facebook**: Official verified company Facebook page.

---

## 🏗️ Technical Architecture

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0 (Async + Sync), SQLite (`leads.db`), Pydantic v2, Pandas, OpenPyXL, HTTPX, BeautifulSoup4, DNSPython.
- **Frontend**: React 18, Tailwind CSS, Lucide Icons, interactive slide-over audit drawer, real-time status polling.
- **Storage**: SQLite database with relational schemas for Jobs, Companies, Evidence Ledger, and Manual Review items.

---

## ⚡ Quick Start on Windows

### 1. Requirements
- **Python 3.13** (detected at `C:\Users\HP\AppData\Local\Programs\Python\Python313\python.exe`)
- Windows 10 or 11

### 2. Run the Application
Simply double-click or run from PowerShell:

```powershell
.\start_app.bat
```

Or run directly with the virtual environment:

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser to:
👉 **`http://localhost:8000`**

---

## 🧪 Testing with Sample Leads

A test dataset with real US roofing businesses is included in the project:
- **`sample_data/roofing_leads_sample.xlsx`**
- **`sample_data/roofing_leads_sample.csv`**

### Steps to Test:
1. Open `http://localhost:8000`.
2. Click **"Upload Leads (XLSX / CSV)"**.
3. Select `sample_data/roofing_leads_sample.xlsx`.
4. Review the instant 10-row preview and confirmed column mappings.
5. Click **"Confirm & Start Automatic Research"**.
6. Watch the live progress bar as each company is researched across all 12 fields.
7. Click **"Evidence & Details"** on any row to inspect the complete audit trail.
8. Click **"Export Excel"** to download the 4-sheet formatted workbook.

---

## 🔑 API & Integration Keys

The application works immediately out-of-the-box using the built-in direct website crawler, DNS MX verifier, and DuckDuckGo fallback adapter.

To enable additional high-precision external search providers, open **API Settings** in the top navigation bar or populate `.env`:

| Provider | Purpose | Status |
| :--- | :--- | :--- |
| **Website Crawler** | Scrapes Home, About, Contact, Team, Services for contacts & socials | Built-in (Always Active) |
| **DNS MX Verifier** | Performs domain mail exchange deliverability verification | Built-in (Always Active) |
| **DuckDuckGo** | Free web search fallback | Active |
| **Gemini / OpenAI** | Semantic AI extraction of decision-makers from search snippets | Optional (API Key) |
| **Tavily** | High-accuracy web research for B2B intelligence | Optional (API Key) |
| **Google Places** | Official business addresses, phone numbers, and ratings | Optional (API Key) |
| **Google Search / Bing / Brave** | Search engine discovery | Optional (API Key) |
| **Apollo / Hunter** | Verified B2B contacts and email delivery status | Optional (API Key) |

