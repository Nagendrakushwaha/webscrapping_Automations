export interface Company {
  id: string;
  job_id: string;
  original_id: string;
  original_name: string;
  original_trades: string;
  original_city: string;
  original_state: string;
  original_phone: string;
  original_website: string;
  original_claimed: string;
  
  official_name: string;
  official_website: string;
  website_status: string;

  // 12 Mandatory Fields
  owner_name: string;
  owner_title: string;
  owner_status: string;
  owner_confidence: number;

  ceo_name: string;
  ceo_title: string;
  ceo_status: string;
  ceo_confidence: number;

  founder_name: string;
  founder_title: string;
  founder_status: string;
  founder_confidence: number;

  cofounder_name: string;
  cofounder_title: string;
  cofounder_status: string;
  cofounder_confidence: number;

  business_email: string;
  business_email_status: string;

  business_phone: string;
  business_phone_status: string;

  personal_email: string;
  personal_email_status: string;
  email_verification_status: string;

  personal_phone: string;
  personal_phone_status: string;

  personal_linkedin: string;
  personal_linkedin_status: string;

  business_linkedin: string;
  business_linkedin_status: string;

  business_instagram: string;
  business_instagram_status: string;

  business_facebook: string;
  business_facebook_status: string;

  overall_confidence_score: number;
  overall_verification_status: string;
  missing_fields: string[];
  research_notes: string;
  last_checked: string;
}

export interface Evidence {
  id: string;
  field_name: string;
  discovered_value: string;
  source_name: string;
  source_url: string;
  discovery_date: string;
  last_checked: string;
  confidence_score: number;
  verification_status: string;
  notes: string;
}

export interface Job {
  id: string;
  filename: string;
  total_companies: number;
  processed_companies: number;
  enriched_count: number;
  fully_verified_count: number;
  partially_verified_count: number;
  unverified_count: number;
  not_found_count: number;
  failed_count: number;
  manual_review_count: number;
  status: string;
  current_company_name: string;
  current_stage: string;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface ApiConfig {
  id: string;
  provider_name: string;
  is_enabled: boolean;
  is_connected: boolean;
  last_tested?: string;
  last_error: string;
  usage_count: number;
  has_key: boolean;
}
