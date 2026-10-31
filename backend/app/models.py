import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    total_companies = Column(Integer, default=0)
    processed_companies = Column(Integer, default=0)
    enriched_count = Column(Integer, default=0)
    fully_verified_count = Column(Integer, default=0)
    partially_verified_count = Column(Integer, default=0)
    unverified_count = Column(Integer, default=0)
    not_found_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    manual_review_count = Column(Integer, default=0)
    
    # Status: pending, processing, paused, stopped, completed, failed
    status = Column(String, default="pending")
    current_company_name = Column(String, default="")
    current_stage = Column(String, default="")
    
    settings_json = Column(Text, default="{}")
    column_mapping_json = Column(Text, default="{}")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    companies = relationship("Company", back_populates="job", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    # 1. Original Columns (PRESERVED INTACT)
    original_id = Column(String, default="")
    original_name = Column(String, default="")
    original_trades = Column(String, default="")
    original_city = Column(String, default="")
    original_state = Column(String, default="")
    original_phone = Column(String, default="")
    original_website = Column(String, default="")
    original_claimed = Column(String, default="")
    raw_data_json = Column(Text, default="{}")

    # 2. Additional Business Identity Details
    official_name = Column(String, default="")
    alternative_name = Column(String, default="")
    trades = Column(String, default="")
    business_category = Column(String, default="")
    business_description = Column(Text, default="")
    city = Column(String, default="")
    state = Column(String, default="")
    country = Column(String, default="USA")
    address = Column(String, default="")
    zip_code = Column(String, default="")
    year_established = Column(String, default="")
    company_size = Column(String, default="")
    
    # Website Information
    official_website = Column(String, default="")
    website_status = Column(String, default="Unverified") # Active, Broken, No Official Website, Redirected, Unverified
    website_title = Column(String, default="")
    website_description = Column(Text, default="")
    contact_page_url = Column(String, default="")
    about_page_url = Column(String, default="")
    team_page_url = Column(String, default="")
    services_page_url = Column(String, default="")

    # Agency & Tech Stack Intelligence (Tex Web Solutions)
    tech_stack_cms = Column(String, default="Custom / Unknown")
    has_ssl = Column(Boolean, default=False)
    is_mobile_responsive = Column(Boolean, default=True)
    has_analytics = Column(Boolean, default=False)
    seo_audit_score = Column(Integer, default=0)
    redesign_opportunity = Column(String, default="Medium") # High, Medium, Low
    phone_line_type = Column(String, default="Landline / Office")
    email_mailbox_provider = Column(String, default="Custom")
    ai_personalized_pitch = Column(Text, default="")

    # 3. Mandatory Decision-Maker Fields (Fields 1-4)
    # Field 1: Owner
    owner_name = Column(String, default="")
    owner_title = Column(String, default="")
    owner_status = Column(String, default="Not Found")
    owner_confidence = Column(Integer, default=0)

    # Field 2: CEO
    ceo_name = Column(String, default="")
    ceo_title = Column(String, default="")
    ceo_status = Column(String, default="Not Found")
    ceo_confidence = Column(Integer, default=0)

    # Field 3: Founder
    founder_name = Column(String, default="")
    founder_title = Column(String, default="")
    founder_status = Column(String, default="Not Found")
    founder_confidence = Column(Integer, default=0)

    # Field 4: Co-Founder
    cofounder_name = Column(String, default="")
    cofounder_title = Column(String, default="")
    cofounder_status = Column(String, default="Not Found")
    cofounder_confidence = Column(Integer, default=0)

    primary_decision_maker = Column(String, default="")
    primary_decision_maker_title = Column(String, default="")

    # 4. Mandatory Contact Information Fields (Fields 5-8)
    # Field 5: Business Email
    business_email = Column(String, default="")
    additional_business_emails = Column(Text, default="[]") # JSON list
    business_email_status = Column(String, default="Not Found")

    # Field 6: Business Phone
    business_phone = Column(String, default="")
    additional_business_phones = Column(Text, default="[]") # JSON list
    business_phone_status = Column(String, default="Not Found")

    # Field 7: Personal Professional Email
    personal_email = Column(String, default="")
    personal_email_status = Column(String, default="Not Found")
    email_verification_status = Column(String, default="Unknown") # Valid, Invalid, Catch-All, Unknown, Not Found

    # Field 8: Public Professional Phone
    personal_phone = Column(String, default="")
    personal_phone_status = Column(String, default="Not Found")

    # 5. Mandatory Social Fields (Fields 9-12)
    # Field 9: Personal LinkedIn
    personal_linkedin = Column(String, default="")
    personal_linkedin_status = Column(String, default="Not Found")

    # Field 10: Business LinkedIn
    business_linkedin = Column(String, default="")
    business_linkedin_status = Column(String, default="Not Found")

    # Field 11: Business Instagram
    business_instagram = Column(String, default="")
    business_instagram_status = Column(String, default="Not Found")

    # Field 12: Business Facebook
    business_facebook = Column(String, default="")
    business_facebook_status = Column(String, default="Not Found")

    # Overall Metrics & Status
    overall_confidence_score = Column(Integer, default=0) # 0-100
    overall_verification_status = Column(String, default="Unverified")
    missing_fields = Column(Text, default="[]") # JSON list of missing fields
    research_notes = Column(Text, default="")
    sources_searched = Column(Text, default="[]") # JSON list of sources
    research_history = Column(Text, default="[]")
    
    last_checked = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="companies")
    evidence = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")
    manual_reviews = relationship("ManualReview", back_populates="company", cascade="all, delete-orphan")
    decision_makers = relationship("DecisionMakerRecord", back_populates="company", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    field_name = Column(String, nullable=False)
    discovered_value = Column(Text, default="")
    source_name = Column(String, default="")
    source_url = Column(Text, default="")
    discovery_date = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Integer, default=0)
    verification_status = Column(String, default="Unverified")
    notes = Column(Text, default="")

    company = relationship("Company", back_populates="evidence")


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    field_name = Column(String, nullable=False)
    conflicting_values = Column(Text, default="[]") # JSON list of strings
    source_urls = Column(Text, default="[]") # JSON list of URLs
    reason = Column(Text, default="")
    suggested_action = Column(Text, default="")
    review_status = Column(String, default="Pending") # Pending, Resolved, Dismissed
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="manual_reviews")


class DecisionMakerRecord(Base):
    __tablename__ = "decision_maker_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String, nullable=False)
    title = Column(String, default="")
    role_type = Column(String, default="") # Owner, CEO, Founder, Co-Founder, President, Executive
    email = Column(String, default="")
    phone = Column(String, default="")
    linkedin_url = Column(String, default="")
    confidence = Column(Integer, default=0)
    verification_status = Column(String, default="Unverified")
    evidence_source = Column(String, default="")

    company = relationship("Company", back_populates="decision_makers")


class ApiConfig(Base):
    __tablename__ = "api_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_name = Column(String, unique=True, nullable=False)
    api_key = Column(String, default="")
    extra_config = Column(Text, default="{}")
    is_enabled = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_tested = Column(DateTime, nullable=True)
    last_error = Column(Text, default="")
    usage_count = Column(Integer, default=0)

