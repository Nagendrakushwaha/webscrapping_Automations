import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from .config import settings, BASE_DIR
from .database import init_db
from .api import (
    jobs_router, companies_router, export_router, 
    settings_router, locations_router, automation_router,
    national_roofing_router
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated Multi-Source B2B Lead Research, Enrichment & Verification System",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jobs_router)
app.include_router(companies_router)
app.include_router(export_router)
app.include_router(settings_router)
app.include_router(locations_router)
app.include_router(automation_router)
app.include_router(national_roofing_router)

# Mount static files if present
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "company": settings.COMPANY_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "company": settings.COMPANY_NAME,
        "docs_url": "/docs"
    }
