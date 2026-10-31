from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

# 1. API Configurations
class ApiConfigOut(BaseModel):
    id: str
    provider_name: str
    is_enabled: bool
    is_connected: bool
    last_tested: Optional[datetime] = None
    last_error: str = ""
    usage_count: int = 0
    has_key: bool = False

    class Config:
        from_attributes = True

class ApiConfigUpdate(BaseModel):
    provider_name: str
    api_key: str
    extra_config: Optional[dict[str, Any]] = None
    is_enabled: bool = True

class ApiTestRequest(BaseModel):
    provider_name: str
    api_key: Optional[str] = None
    extra_config: Optional[dict[str, Any]] = None

class ApiTestResponse(BaseModel):
    provider_name: str
    success: bool
    message: str

# 2. Excel Preview & Column Mapping
class ColumnMappingRequest(BaseModel):
    file_id: str
    mappings: dict[str, str] # e.g. {"name": "Company Name", "city": "City"}
    settings: Optional[dict[str, Any]] = None

class PreviewResponse(BaseModel):
    file_id: str
    filename: str
    total_rows: int
    headers: list[str]
    preview_rows: list[dict[str, Any]]
    detected_mappings: dict[str, str]
    duplicate_count: int

# 3. Research Settings
class ResearchSettingsSchema(BaseModel):
    industry: str = "Roofing"
    country: str = "USA"
    state: Optional[str] = ""
    city: Optional[str] = ""
    concurrency: int = 3
    batch_size: int = 50
    max_search_attempts: int = 3
    enabled_sources: list[str] = Field(default_factory=lambda: [
        "website", "tavily", "google_search", "google_places", 
        "bing", "brave", "duckduckgo", "apollo", "hunter"
    ])
    attempt_all_12_fields: bool = True

# 4. Evidence & Manual Review
class EvidenceOut(BaseModel):
    id: str
    field_name: str
    discovered_value: str
    source_name: str
    source_url: str
    discovery_date: datetime
    last_checked: datetime
    confidence_score: int
    verification_status: str
    notes: str

    class Config:
        from_attributes = True

class ManualReviewOut(BaseModel):
    id: str
    company_id: str
    field_name: str
    conflicting_values: list[str]
    source_urls: list[str]
    reason: str
    suggested_action: str
    review_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ManualReviewResolve(BaseModel):
    selected_value: str
    review_status: str = "Resolved" # Resolved, Dismissed

class DecisionMakerOut(BaseModel):
    id: str
    name: str
    title: str
    role_type: str
    email: str
    phone: str
    linkedin_url: str
    confidence: int
    verification_status: str
    evidence_source: str

    class Config:
        from_attributes = True

# 5. Company Schemas
class CompanyOut(BaseModel):
    id: str
    job_id: str
    original_id: str
    original_name: str
    original_trades: str
    original_city: str
    original_state: str
    original_phone: str
    original_website: str
    original_claimed: str
    
    # Discovered
    official_name: str
    official_website: str
    website_status: str
    
    # 12 Mandatory Fields
    owner_name: str
    owner_title: str
    owner_status: str
    owner_confidence: int
    
    ceo_name: str
    ceo_title: str
    ceo_status: str
    ceo_confidence: int
    
    founder_name: str
    founder_title: str
    founder_status: str
    founder_confidence: int
    
    cofounder_name: str
    cofounder_title: str
    cofounder_status: str
    cofounder_confidence: int
    
    business_email: str
    business_email_status: str
    
    business_phone: str
    business_phone_status: str
    
    personal_email: str
    personal_email_status: str
    email_verification_status: str
    
    personal_phone: str
    personal_phone_status: str
    
    personal_linkedin: str
    personal_linkedin_status: str
    
    business_linkedin: str
    business_linkedin_status: str
    
    business_instagram: str
    business_instagram_status: str
    
    business_facebook: str
    business_facebook_status: str

    # Agency & Tech Stack Intelligence
    tech_stack_cms: str = "Custom / Unknown"
    has_ssl: bool = False
    is_mobile_responsive: bool = True
    has_analytics: bool = False
    seo_audit_score: int = 0
    redesign_opportunity: str = "Medium"
    phone_line_type: str = "Landline / Office"
    email_mailbox_provider: str = "Custom"
    ai_personalized_pitch: str = ""
    
    overall_confidence_score: int
    overall_verification_status: str
    missing_fields: list[str]
    research_notes: str
    last_checked: datetime

    class Config:
        from_attributes = True

class CompanyDetailOut(CompanyOut):
    address: str
    zip_code: str
    year_established: str
    company_size: str
    website_title: str
    website_description: str
    contact_page_url: str
    about_page_url: str
    team_page_url: str
    services_page_url: str
    additional_business_emails: list[str]
    additional_business_phones: list[str]
    sources_searched: list[str]
    evidence: list[EvidenceOut] = []
    manual_reviews: list[ManualReviewOut] = []
    decision_makers: list[DecisionMakerOut] = []

    class Config:
        from_attributes = True

# 6. Job Schemas
class JobOut(BaseModel):
    id: str
    filename: str
    total_companies: int
    processed_companies: int
    enriched_count: int
    fully_verified_count: int
    partially_verified_count: int
    unverified_count: int
    not_found_count: int
    failed_count: int
    manual_review_count: int
    status: str
    current_company_name: str
    current_stage: str
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobControlRequest(BaseModel):
    action: str # start, pause, resume, stop, retry_failed

