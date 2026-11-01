const { useState, useEffect, useRef } = React;

// --- API Helpers ---
const API_BASE = "";

async function apiFetch(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API Request Failed");
  }
  return res.json();
}

// Industry Presets
const PRESET_INDUSTRIES = [
  "Roofing Contractors",
  "Commercial Roofing",
  "Residential Roofing",
  "Solar Energy Contractors",
  "HVAC & Air Conditioning",
  "Plumbing Contractors",
  "Electrical Contractors",
  "General Contractors",
  "Landscaping & Tree Service",
  "Painting Contractors",
  "Remodeling & Home Improvement",
  "Paving & Concrete"
];

function App() {
  // Navigation: 'dashboard' | 'enrichment' | 'automation' | 'history' | 'settings'
  const [activeTab, setActiveTab] = useState("automation");

  // Global & Jobs State
  const [jobs, setJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(15);

  // Filters for standard lead management
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [hasOwnerFilter, setHasOwnerFilter] = useState(null);
  const [hasEmailFilter, setHasEmailFilter] = useState(null);
  const [hasLinkedInFilter, setHasLinkedInFilter] = useState(null);

  // Drawer & Detail Modal
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [companyDetail, setCompanyDetail] = useState(null);
  const [drawerTab, setDrawerTab] = useState("mandatory"); // mandatory, pitch, evidence, audit, sos, raw
  const [pitchCopied, setPitchCopied] = useState(false);

  // Upload & Mapping Flow (Lead Enrichment)
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [columnMappings, setColumnMappings] = useState({});
  const [uploadLoading, setUploadLoading] = useState(false);

  // API Settings State
  const [apiModalOpen, setApiModalOpen] = useState(false);
  const [apiConfigs, setApiConfigs] = useState([]);
  const [testingProvider, setTestingProvider] = useState(null);
  const [testResult, setTestResult] = useState({});

  // ------------------------------------------------------------------------
  // AUTOMATED LEAD GENERATION STATE
  // ------------------------------------------------------------------------
  const [usStates, setUsStates] = useState([]);
  const [availableCities, setAvailableCities] = useState([]);
  const [loadingCities, setLoadingCities] = useState(false);
  const [activeAutomationId, setActiveAutomationId] = useState(null);
  const [activeAutomation, setActiveAutomation] = useState(null);
  const [automationHistory, setAutomationHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [automationLeads, setAutomationLeads] = useState([]);
  const [totalAutomationLeads, setTotalAutomationLeads] = useState(0);
  const [automationLeadsPage, setAutomationLeadsPage] = useState(1);
  const [automationFilterMinScore, setAutomationFilterMinScore] = useState(0);
  const [automationFilterRedesignOnly, setAutomationFilterRedesignOnly] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  };

  // Search Configuration Form
  const [searchMode, setSearchMode] = useState("cities"); // 'cities' | 'entire_state'
  const [selectedStates, setSelectedStates] = useState(["TX"]);
  const [selectedCities, setSelectedCities] = useState(["Houston"]);
  const [citySearchInput, setCitySearchInput] = useState("");
  const [searchRadius, setSearchRadius] = useState(50);
  const [selectedIndustries, setSelectedIndustries] = useState(["Roofing Contractors"]);
  const [customIndustryInput, setCustomIndustryInput] = useState("");
  const [targetLeads, setTargetLeads] = useState(100);

  // Lead Quality & Agency Opportunity Filters
  const [agencyFilters, setAgencyFilters] = useState({
    require_redesign_opportunity: false,
    missing_website_only: false,
    outdated_cms_only: false,
    require_decision_maker: false,
    require_email: false,
    require_phone: false
  });

  // ------------------------------------------------------------------------
  // NATIONAL ROOFING DIRECTORY STATE
  // ------------------------------------------------------------------------
  const [nationalJobId, setNationalJobId] = useState(null);
  const [nationalJob, setNationalJob] = useState(null);
  const [nationalHistory, setNationalHistory] = useState([]);
  const [nationalLeads, setNationalLeads] = useState([]);
  const [nationalTotalLeads, setNationalTotalLeads] = useState(0);
  const [nationalPage, setNationalPage] = useState(1);
  const [nationalTotalPages, setNationalTotalPages] = useState(1);
  const [nationalSearch, setNationalSearch] = useState("");
  const [nationalFilterCity, setNationalFilterCity] = useState("All");
  const [nationalFilterQuick, setNationalFilterQuick] = useState("all"); // 'all' | 'gmail' | 'email' | 'phone' | 'website' | 'missing_website'
  const [nationalState, setNationalState] = useState("Texas");
  const [nationalStateCode, setNationalStateCode] = useState("TX");
  const [nationalTargetLeads, setNationalTargetLeads] = useState(100);
  const [nationalAvailableCities, setNationalAvailableCities] = useState([]);
  const [nationalSelectedCities, setNationalSelectedCities] = useState([]);
  const [nationalLoadingCities, setNationalLoadingCities] = useState(false);
  const [nationalSelectedLeadIds, setNationalSelectedLeadIds] = useState([]);

  // Providers Selection
  const [discoveryProviders, setDiscoveryProviders] = useState({
    the_roofing_list: true,
    openstreetmap: true,
    google_places: true,
    search_engines: true
  });

  // Mini-CRM & Selection State
  const [selectedLeadIds, setSelectedLeadIds] = useState([]);
  const [webhookUrl, setWebhookUrl] = useState(() => localStorage.getItem("saved_webhook_url") || "");
  const [proxyUrl, setProxyUrl] = useState(() => localStorage.getItem("saved_proxy_url") || "");

  // ------------------------------------------------------------------------
  // INITIAL DATA LOADING
  // ------------------------------------------------------------------------
  useEffect(() => {
    loadJobs();
    loadApiConfigs();
    loadUSStates();
    loadAutomationHistory();

    const interval = setInterval(() => {
      // Background poll current job or active automation
      if (currentJob && currentJob.status === "processing") {
        refreshJobStatus(currentJob.id);
      }
      if (activeAutomationId) {
        refreshAutomationStatus(activeAutomationId);
      }
      if (nationalJobId && (nationalJob?.status === "running" || activeTab === "national_roofing")) {
        apiFetch(`/api/national-roofing/jobs/${nationalJobId}`).then(j => {
          setNationalJob(j);
          if (j.status === "running" || j.status === "completed") {
            loadNationalLeads(nationalJobId, nationalPage);
          }
        }).catch(() => {});
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [currentJob, activeAutomationId]);

  // Load cities when selectedStates change
  useEffect(() => {
    if (selectedStates.length > 0) {
      loadCitiesForStates(selectedStates);
    } else {
      setAvailableCities([]);
      setSelectedCities([]);
    }
  }, [selectedStates]);

  const loadUSStates = async () => {
    try {
      const data = await apiFetch("/api/locations/states");
      setUsStates(data.states || []);
    } catch (e) {
      console.error("Failed to load US states:", e);
    }
  };

  const loadCitiesForStates = async (states) => {
    setLoadingCities(true);
    try {
      const query = states.map(s => `states=${encodeURIComponent(s)}`).join("&");
      const data = await apiFetch(`/api/locations/cities/multi?${query}&limit=250`);
      setAvailableCities(data.cities || []);
    } catch (e) {
      console.error("Failed to load cities:", e);
    } finally {
      setLoadingCities(false);
    }
  };

  const loadJobs = async () => {
    try {
      const data = await apiFetch("/api/jobs");
      setJobs(data);
      if (data.length > 0 && !currentJob) {
        setCurrentJob(data[0]);
      }
    } catch (e) {
      console.error("Failed to load jobs:", e);
    }
  };

  const loadApiConfigs = async () => {
    try {
      const data = await apiFetch("/api/settings/api-keys");
      setApiConfigs(data);
    } catch (e) {
      console.error("Failed to load API keys:", e);
    }
  };

  const loadAutomationHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await apiFetch("/api/automation/history?limit=25");
      setAutomationHistory(data.history || []);
      if (!activeAutomationId && data.history && data.history.length > 0) {
        // Find latest running or recent automation
        const running = data.history.find(h => h.status === "RUNNING" || h.status === "PAUSED");
        const target = running || data.history[0];
        setActiveAutomationId(target.id);
        setActiveAutomation(target);
      }
    } catch (e) {
      console.error("Failed to load automation history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const refreshJobStatus = async (jobId) => {
    try {
      const data = await apiFetch(`/api/jobs/${jobId}`);
      setCurrentJob(data);
      if (data.status === "completed" || data.status === "failed") {
        loadCompanies(jobId, currentPage);
      }
    } catch (e) {
      console.error("Failed to poll job:", e);
    }
  };

  const refreshAutomationStatus = async (automationId) => {
    try {
      const data = await apiFetch(`/api/automation/${automationId}`);
      setActiveAutomation(data);
      // Refresh lead table
      loadAutomationLeads(automationId, automationLeadsPage);
    } catch (e) {
      console.error("Failed to refresh automation status:", e);
    }
  };

  // ------------------------------------------------------------------------
  // NATIONAL ROOFING DIRECTORY HANDLERS
  // ------------------------------------------------------------------------
  const loadNationalCities = async (st = nationalState) => {
    setNationalLoadingCities(true);
    try {
      const data = await apiFetch(`/api/national-roofing/cities?state=${encodeURIComponent(st)}`);
      setNationalAvailableCities(data.cities || []);
    } catch (e) {
      console.error("Failed to discover National Roofing cities:", e);
    } finally {
      setNationalLoadingCities(false);
    }
  };

  const loadNationalJobs = async () => {
    try {
      const jobs = await apiFetch("/api/national-roofing/jobs");
      setNationalHistory(jobs || []);
      if (!nationalJobId && jobs && jobs.length > 0) {
        setNationalJobId(jobs[0].id);
        setNationalJob(jobs[0]);
        loadNationalLeads(jobs[0].id, 1);
      }
    } catch (e) {
      console.error("Failed to load National Roofing jobs:", e);
    }
  };

  const loadNationalLeads = async (jobId = nationalJobId, page = 1) => {
    if (!jobId) return;
    try {
      let url = `/api/national-roofing/jobs/${jobId}/leads?page=${page}&page_size=25`;
      if (nationalSearch) url += `&search=${encodeURIComponent(nationalSearch)}`;
      if (nationalFilterCity && nationalFilterCity !== "All") url += `&city=${encodeURIComponent(nationalFilterCity)}`;
      if (nationalFilterQuick === "gmail") url += `&has_gmail=true`;
      if (nationalFilterQuick === "email") url += `&has_email=true`;
      if (nationalFilterQuick === "phone") url += `&has_phone=true`;
      if (nationalFilterQuick === "website") url += `&has_website=true`;
      if (nationalFilterQuick === "missing_website") url += `&missing_website=true`;

      const data = await apiFetch(url);
      setNationalLeads(data.leads || []);
      setNationalTotalLeads(data.total || 0);
      setNationalPage(data.page || 1);
      setNationalTotalPages(data.total_pages || 1);
      if (data.job) setNationalJob(data.job);
    } catch (e) {
      console.error("Failed to load National Roofing leads:", e);
    }
  };

  const handleStartNationalScraping = async () => {
    try {
      const res = await apiFetch("/api/national-roofing/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: nationalState,
          state_code: nationalStateCode,
          cities: nationalSelectedCities,
          target_leads: nationalTargetLeads
        })
      });
      setNationalJobId(res.id);
      setNationalJob(res);
      showToast(`National Roofing Scraper Started! Target: ${nationalTargetLeads} in ${nationalState}`, "success");
      loadNationalJobs();
    } catch (e) {
      showToast("Error starting scraper: " + e.message, "error");
    }
  };

  const handlePauseNationalScraping = async () => {
    if (!nationalJobId) return;
    try {
      const res = await apiFetch(`/api/national-roofing/jobs/${nationalJobId}/pause`, { method: "POST" });
      setNationalJob(res);
      showToast("Scraping paused. Checkpoint saved.", "info");
    } catch (e) {
      showToast("Error pausing: " + e.message, "error");
    }
  };

  const handleResumeNationalScraping = async () => {
    if (!nationalJobId) return;
    try {
      const res = await apiFetch(`/api/national-roofing/jobs/${nationalJobId}/resume`, { method: "POST" });
      setNationalJob(res);
      showToast("Scraping resumed from checkpoint.", "success");
    } catch (e) {
      showToast("Error resuming: " + e.message, "error");
    }
  };

  const handleStopNationalScraping = async () => {
    if (!nationalJobId) return;
    if (!confirm("Are you sure you want to stop this scraping job?")) return;
    try {
      const res = await apiFetch(`/api/national-roofing/jobs/${nationalJobId}/stop`, { method: "POST" });
      setNationalJob(res);
      showToast("Scraping stopped.", "info");
    } catch (e) {
      showToast("Error stopping: " + e.message, "error");
    }
  };

  const handleRetryFailedNational = async () => {
    if (!nationalJobId) return;
    try {
      const res = await apiFetch(`/api/national-roofing/jobs/${nationalJobId}/retry-failed`, { method: "POST" });
      setNationalJob(res);
      showToast("Retrying failed contractor profiles.", "info");
    } catch (e) {
      showToast("Error retrying: " + e.message, "error");
    }
  };

  const loadAutomationLeads = async (automationId, page = 1) => {
    if (!automationId) return;
    try {
      let url = `/api/automation/${automationId}/leads?page=${page}&page_size=20`;
      if (automationFilterMinScore > 0) {
        url += `&min_score=${automationFilterMinScore}`;
      }
      if (automationFilterRedesignOnly) {
        url += `&redesign_only=true`;
      }
      const data = await apiFetch(url);
      setAutomationLeads(data.leads || []);
      setTotalAutomationLeads(data.total || 0);
      setAutomationLeadsPage(page);
    } catch (e) {
      console.error("Failed to load automation leads:", e);
    }
  };

  // ------------------------------------------------------------------------
  // MINI-CRM & PIPELINE ACTIONS
  // ------------------------------------------------------------------------
  const handleToggleSelectLead = (id) => {
    setSelectedLeadIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleSelectAllLeads = (e) => {
    if (e.target.checked) {
      setSelectedLeadIds(automationLeads.map(l => l.id));
    } else {
      setSelectedLeadIds([]);
    }
  };

  const handleUpdateLeadStatus = async (companyId, newStatus) => {
    try {
      await apiFetch(`/api/companies/${companyId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      setAutomationLeads(prev => prev.map(l => l.id === companyId ? { ...l, lead_status: newStatus } : l));
    } catch (e) {
      alert("Error updating status: " + e.message);
    }
  };

  const handleToggleStar = async (companyId) => {
    try {
      const res = await apiFetch(`/api/companies/${companyId}/star`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      setAutomationLeads(prev => prev.map(l => l.id === companyId ? { ...l, is_starred: res.is_starred } : l));
    } catch (e) {
      console.error("Error toggling star:", e);
    }
  };

  const handleBulkStatus = async (status) => {
    if (selectedLeadIds.length === 0) return;
    try {
      await apiFetch("/api/companies/bulk-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_ids: selectedLeadIds, action: "update_status", status })
      });
      setAutomationLeads(prev => prev.map(l => selectedLeadIds.includes(l.id) ? { ...l, lead_status: status } : l));
      setSelectedLeadIds([]);
      alert(`Updated status to '${status}' for ${selectedLeadIds.length} leads.`);
    } catch (e) {
      alert("Bulk update error: " + e.message);
    }
  };

  const handleBulkWebhookPush = async () => {
    if (selectedLeadIds.length === 0) return;
    let url = webhookUrl;
    if (!url) {
      url = prompt("Enter Webhook URL (Zapier, Make, n8n, or CRM):");
      if (!url) return;
      setWebhookUrl(url);
      localStorage.setItem("saved_webhook_url", url);
    }
    try {
      const res = await apiFetch("/api/companies/bulk-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_ids: selectedLeadIds, action: "webhook_push", webhook_url: url })
      });
      alert(res.message);
      setSelectedLeadIds([]);
    } catch (e) {
      alert("Webhook push error: " + e.message);
    }
  };

  // ------------------------------------------------------------------------
  // AUTOMATION CONTROLS
  // ------------------------------------------------------------------------
  const handleStartAutomation = async () => {
    if (selectedStates.length === 0) {
      alert("Please select at least one US State.");
      return;
    }
    if (searchMode === "cities" && selectedCities.length === 0) {
      alert("Please select at least one city or choose 'Entire State' search mode.");
      return;
    }
    if (selectedIndustries.length === 0) {
      alert("Please select at least one industry or trade.");
      return;
    }

    const payload = {
      search_mode: searchMode,
      states: selectedStates,
      cities: searchMode === "cities" ? selectedCities : [],
      radius_miles: Number(searchRadius),
      industries: selectedIndustries,
      target_leads: Number(targetLeads),
      providers: Object.keys(discoveryProviders).filter(k => discoveryProviders[k]),
      filters: agencyFilters
    };

    try {
      const res = await apiFetch("/api/automation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      setActiveAutomationId(res.automation_id);
      setActiveAutomation(res);
      loadAutomationHistory();
      showToast(`Automated Lead Generation Started! Target: ${targetLeads} leads in ${selectedStates.join(", ")}`, "success");
    } catch (e) {
      showToast("Error starting automation: " + e.message, "error");
    }
  };

  const handlePauseAutomation = async () => {
    if (!activeAutomationId) return;
    try {
      await apiFetch(`/api/automation/${activeAutomationId}/pause`, { method: "POST" });
      refreshAutomationStatus(activeAutomationId);
    } catch (e) {
      alert("Error pausing: " + e.message);
    }
  };

  const handleResumeAutomation = async () => {
    if (!activeAutomationId) return;
    try {
      await apiFetch(`/api/automation/${activeAutomationId}/resume`, { method: "POST" });
      refreshAutomationStatus(activeAutomationId);
    } catch (e) {
      alert("Error resuming: " + e.message);
    }
  };

  const handleStopAutomation = async () => {
    if (!activeAutomationId) return;
    if (!confirm("Are you sure you want to stop this automation job?")) return;
    try {
      await apiFetch(`/api/automation/${activeAutomationId}/stop`, { method: "POST" });
      refreshAutomationStatus(activeAutomationId);
    } catch (e) {
      alert("Error stopping: " + e.message);
    }
  };

  const handleRetryFailed = async () => {
    if (!activeAutomationId) return;
    try {
      await apiFetch(`/api/automation/${activeAutomationId}/retry-failed`, { method: "POST" });
      refreshAutomationStatus(activeAutomationId);
      alert("Retrying failed leads enrichment.");
    } catch (e) {
      alert("Error retrying: " + e.message);
    }
  };

  // ------------------------------------------------------------------------
  // COMPANY DETAIL MODAL / DRAWER
  // ------------------------------------------------------------------------
  const handleOpenCompanyDetail = async (companyId) => {
    setSelectedCompanyId(companyId);
    try {
      const data = await apiFetch(`/api/companies/${companyId}`);
      setCompanyDetail(data);
      setDrawerTab("mandatory");
    } catch (e) {
      alert("Failed to load lead details: " + e.message);
    }
  };

  // Copy helper
  const copyPitchToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setPitchCopied(true);
    setTimeout(() => setPitchCopied(false), 2000);
  };

  // Helper for Opportunity Score Badge
  const renderScoreBadge = (score, reason) => {
    let color = "bg-rose-950 text-rose-300 border-rose-800";
    let label = "Low";
    if (score >= 70) {
      color = "bg-emerald-950 text-emerald-300 border-emerald-800";
      label = "High Priority";
    } else if (score >= 45) {
      color = "bg-amber-950 text-amber-300 border-amber-800";
      label = "Medium";
    }
    return (
      <div className="flex items-center space-x-1.5" title={reason || `Opportunity Score: ${score}/100`}>
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border ${color}`}>
          {score}/100
        </span>
        <span className="text-[10px] text-slate-400 hidden xl:inline">{label}</span>
      </div>
    );
  };

  // ------------------------------------------------------------------------
  // STANDARD ENRICHMENT UPLOAD FLOW
  // ------------------------------------------------------------------------
  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadFile(file);
    setUploadLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await apiFetch("/api/jobs/preview", {
        method: "POST",
        body: formData
      });
      setPreviewData(data);
      const mappings = { ...(data.detected_mappings || {}) };
      // Normalize website_url
      if (!mappings["website_url"] && mappings["webssite url"]) {
        mappings["website_url"] = mappings["webssite url"];
      }
      setColumnMappings(mappings);
    } catch (err) {
      alert("Failed to parse file preview: " + err.message);
      setUploadFile(null);
    } finally {
      setUploadLoading(false);
      if (e.target) e.target.value = "";
    }
  };

  const handleConfirmMappingAndStart = async () => {
    if (!uploadFile) return;
    setUploadLoading(true);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("column_mapping", JSON.stringify(columnMappings));

    try {
      const newJob = await apiFetch("/api/jobs/upload", {
        method: "POST",
        body: formData
      });
      setUploadModalOpen(false);
      setUploadFile(null);
      setPreviewData(null);
      await loadJobs();
      setCurrentJob(newJob);
      setActiveTab("enrichment");
      alert(`Job created with ${newJob.total_companies} companies! Starting automated research.`);
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const loadCompanies = async (jobId, page = 1) => {
    if (!jobId) return;
    try {
      let url = `/api/companies/job/${jobId}?page=${page}&page_size=${pageSize}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      if (statusFilter !== "All") url += `&status=${encodeURIComponent(statusFilter)}`;
      if (hasOwnerFilter !== null) url += `&has_owner=${hasOwnerFilter}`;
      if (hasEmailFilter !== null) url += `&has_email=${hasEmailFilter}`;
      if (hasLinkedInFilter !== null) url += `&has_linkedin=${hasLinkedInFilter}`;

      const data = await apiFetch(url);
      setCompanies(data.companies || []);
      setTotalCompanies(data.total || 0);
      setCurrentPage(data.page || 1);
      setTotalPages(data.total_pages || 1);
    } catch (e) {
      console.error("Failed to load companies:", e);
    }
  };

  // API Key handlers
  const handleSaveApiKey = async (provider, key) => {
    try {
      await apiFetch("/api/settings/api-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_name: provider, api_key: key })
      });
      alert(`API Key for ${provider} saved!`);
      loadApiConfigs();
    } catch (e) {
      alert("Failed to save key: " + e.message);
    }
  };

  const handleTestApi = async (provider, key) => {
    setTestingProvider(provider);
    try {
      const res = await apiFetch("/api/settings/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_name: provider, api_key: key })
      });
      setTestResult(prev => ({ ...prev, [provider]: res }));
    } catch (e) {
      setTestResult(prev => ({ ...prev, [provider]: { success: false, message: e.message } }));
    } finally {
      setTestingProvider(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Alert Banner */}
      {toast && (
        <div className={`fixed top-5 right-6 z-50 flex items-center space-x-3 px-5 py-3 rounded-xl shadow-2xl border backdrop-blur-md text-sm font-semibold transition-all ${
          toast.type === "error" ? "bg-red-950/90 text-red-200 border-red-800" : "bg-blue-600/95 text-white border-blue-400/40"
        }`}>
          <span>{toast.type === "error" ? "⚠️" : "🚀"}</span>
          <span>{toast.message}</span>
        </div>
      )}
      {/* ------------------------------------------------------------- */}
      {/* HEADER / NAVIGATION                                          */}
      {/* ------------------------------------------------------------- */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-black text-xl text-white shadow-lg shadow-blue-500/20">
            T
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">AI LEAD INTELLIGENCE</h1>
              <span className="text-[10px] bg-blue-500/20 text-blue-300 font-semibold px-2 py-0.5 rounded border border-blue-500/30">
                PRO v2.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Tex Web Solutions Pvt. Ltd. &bull; Automated B2B Lead Engine
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "dashboard"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => setActiveTab("enrichment")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "enrichment"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            ⚡ Lead Enrichment
          </button>
          <button
            onClick={() => setActiveTab("automation")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === "automation"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>🚀 Automated Lead Generation</span>
          </button>
          <button
            onClick={() => {
              setActiveTab("national_roofing");
              loadNationalJobs();
              if (nationalAvailableCities.length === 0) loadNationalCities(nationalState);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === "national_roofing"
                ? "bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-md shadow-orange-500/20"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            <span>🏢 National Roofing Directory</span>
            <span className="text-[9px] bg-amber-500/30 text-amber-200 px-1 py-0.2 rounded font-bold uppercase">New</span>
          </button>
          <button
            onClick={() => {
              setActiveTab("history");
              loadAutomationHistory();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "history"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            📜 Automation History
          </button>
          <button
            onClick={() => setApiModalOpen(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          >
            ⚙️ API Settings
          </button>
        </nav>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: AUTOMATED LEAD GENERATION (PRIMARY NEW MODULE)         */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "automation" && (
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-blue-400">
                  Targeted B2B Acquisition Module
                </span>
                <h2 className="text-2xl font-black text-white mt-1">
                  Location-Based Automated Lead Discovery
                </h2>
                <p className="text-sm text-slate-400 mt-1 max-w-2xl">
                  Select US States and Cities from the official US Census Bureau database. Discover local businesses via OpenStreetMap, Google Places, and search engines. Enriches decision-makers (Owner/CEO), emails, direct phone lines, tech stack, and Web Redesign Opportunity Scores automatically.
                </p>
              </div>

              {/* Status / Quick Action */}
              <div className="flex items-center space-x-3">
                {activeAutomation && activeAutomation.status === "RUNNING" && (
                  <div className="flex items-center space-x-2 bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 px-3.5 py-2 rounded-xl text-xs font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    <span>RUNNING ({activeAutomation.discovered_count} found)</span>
                  </div>
                )}
                {activeAutomation && activeAutomation.status === "PAUSED" && (
                  <div className="flex items-center space-x-2 bg-amber-950/80 border border-amber-700/60 text-amber-300 px-3.5 py-2 rounded-xl text-xs font-semibold">
                    <span>PAUSED</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* TWO COLUMN GRID: Configuration on Left (4 cols), Live Monitor on Right (8 cols) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT COLUMN: Search & Filter Controls */}
            <div className="lg:col-span-5 space-y-6">
              {/* 1. Location Selection */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <span>📍 1. US Location Selection</span>
                  </h3>
                  <div className="flex items-center space-x-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800">
                    <button
                      onClick={() => setSearchMode("cities")}
                      className={`px-2.5 py-1 text-[11px] font-semibold rounded ${
                        searchMode === "cities" ? "bg-blue-600 text-white" : "text-slate-400"
                      }`}
                    >
                      Selected Cities
                    </button>
                    <button
                      onClick={() => setSearchMode("entire_state")}
                      className={`px-2.5 py-1 text-[11px] font-semibold rounded ${
                        searchMode === "entire_state" ? "bg-blue-600 text-white" : "text-slate-400"
                      }`}
                    >
                      Entire State
                    </button>
                  </div>
                </div>

                {/* State Selection */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Target US State(s) ({usStates.length} Official States + DC)
                  </label>
                  <select
                    value={selectedStates[0] || "TX"}
                    onChange={(e) => {
                      const val = e.target.value;
                      setSelectedStates([val]);
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    {usStates.map((st) => (
                      <option key={st.abbr} value={st.abbr}>
                        {st.name} ({st.abbr}) — Capital: {st.capital}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Cities Multi-Select (When in 'cities' mode) */}
                {searchMode === "cities" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-slate-300">
                        Cities in {selectedStates.join(", ")}
                      </label>
                      <button
                        onClick={() => {
                          const allNames = availableCities.map(c => c.city_name);
                          setSelectedCities(allNames);
                        }}
                        className="text-[10px] text-blue-400 hover:underline"
                      >
                        Select All ({availableCities.length})
                      </button>
                    </div>

                    {/* Filter search box for cities */}
                    <input
                      type="text"
                      placeholder="Filter city list (e.g. Houston, Dallas)..."
                      value={citySearchInput}
                      onChange={(e) => setCitySearchInput(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    />

                    {/* Scrollable City Checkboxes */}
                    <div className="max-h-44 overflow-y-auto bg-slate-950 border border-slate-800 rounded-xl p-2.5 space-y-1.5 custom-scrollbar">
                      {loadingCities ? (
                        <div className="text-center py-4 text-xs text-slate-500">
                          Loading Census cities...
                        </div>
                      ) : availableCities.length === 0 ? (
                        <div className="text-center py-4 text-xs text-slate-500">
                          No cities found for selected state.
                        </div>
                      ) : (
                        availableCities
                          .filter(c => c.city_name.toLowerCase().includes(citySearchInput.toLowerCase()))
                          .map((city) => {
                            const isChecked = selectedCities.includes(city.city_name);
                            return (
                              <label
                                key={city.id}
                                className={`flex items-center justify-between p-1.5 rounded-lg cursor-pointer text-xs transition ${
                                  isChecked ? "bg-blue-950/40 text-blue-200" : "hover:bg-slate-900 text-slate-300"
                                }`}
                              >
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="checkbox"
                                    checked={isChecked}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedCities([...selectedCities, city.city_name]);
                                      } else {
                                        setSelectedCities(selectedCities.filter(c => c !== city.city_name));
                                      }
                                    }}
                                    className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
                                  />
                                  <span>{city.city_name}</span>
                                </div>
                                <span className="text-[10px] text-slate-500">
                                  {city.population ? `${city.population.toLocaleString()} pop` : city.place_type}
                                </span>
                              </label>
                            );
                          })
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400">
                      Selected {selectedCities.length} {selectedCities.length === 1 ? "city" : "cities"}.
                    </p>
                  </div>
                )}

                {/* Geographical Radius Slider & Presets */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-slate-300">
                      Search Radius: <span className="text-blue-400 font-bold">{searchRadius} miles</span>
                    </label>
                    <span className="text-[10px] text-slate-500">
                      Auto zone-tiling active for &gt; 30mi
                    </span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={searchRadius}
                    onChange={(e) => setSearchRadius(Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                  <div className="flex items-center justify-between mt-2">
                    {[10, 25, 50, 75, 100].map((r) => (
                      <button
                        key={r}
                        onClick={() => setSearchRadius(r)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          searchRadius === r
                            ? "bg-blue-600 border-blue-500 text-white"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {r} mi
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 2. Industry & Trade Selection */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-white">
                    🏢 2. Industry & Trade Selection
                  </h3>
                  <span className="text-[10px] text-slate-400">
                    {selectedIndustries.length} Selected
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {PRESET_INDUSTRIES.map((ind) => {
                    const isSelected = selectedIndustries.includes(ind);
                    return (
                      <button
                        key={ind}
                        onClick={() => {
                          if (isSelected) {
                            if (selectedIndustries.length > 1) {
                              setSelectedIndustries(selectedIndustries.filter(i => i !== ind));
                            }
                          } else {
                            setSelectedIndustries([...selectedIndustries, ind]);
                          }
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                          isSelected
                            ? "bg-blue-600/20 border-blue-500 text-blue-200"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        {isSelected ? "✓ " : "+ "}
                        {ind}
                      </button>
                    );
                  })}
                </div>

                {/* Custom Industry Input */}
                <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/80">
                  <input
                    type="text"
                    placeholder="Add custom trade/industry..."
                    value={customIndustryInput}
                    onChange={(e) => setCustomIndustryInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && customIndustryInput.trim()) {
                        setSelectedIndustries([...selectedIndustries, customIndustryInput.trim()]);
                        setCustomIndustryInput("");
                      }
                    }}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => {
                      if (customIndustryInput.trim()) {
                        setSelectedIndustries([...selectedIndustries, customIndustryInput.trim()]);
                        setCustomIndustryInput("");
                      }
                    }}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* 3. Lead Quantity & Agency Filters */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-3">
                  🎯 3. Lead Targets & Web Agency Filters
                </h3>

                {/* Target Count */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-slate-300">
                      Target Leads: <span className="text-blue-400 font-bold">{targetLeads} leads</span>
                    </label>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="1000"
                    step="25"
                    value={targetLeads}
                    onChange={(e) => setTargetLeads(Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                  <div className="flex items-center justify-between mt-2">
                    {[50, 100, 250, 500, 1000].map((t) => (
                      <button
                        key={t}
                        onClick={() => setTargetLeads(t)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          targetLeads === t
                            ? "bg-blue-600 border-blue-500 text-white"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Agency-Specific Opportunity Checkboxes */}
                <div className="space-y-2 pt-2 border-t border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                    Tex Web Solutions Lead Filters:
                  </span>

                  <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agencyFilters.require_redesign_opportunity}
                      onChange={(e) => setAgencyFilters({ ...agencyFilters, require_redesign_opportunity: e.target.checked })}
                      className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <span>Highlight high-value Website Redesign opportunities</span>
                  </label>

                  <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agencyFilters.missing_website_only}
                      onChange={(e) => setAgencyFilters({ ...agencyFilters, missing_website_only: e.target.checked })}
                      className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <span>Prioritize businesses with NO website (100% Greenfield sale)</span>
                  </label>

                  <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agencyFilters.outdated_cms_only}
                      onChange={(e) => setAgencyFilters({ ...agencyFilters, outdated_cms_only: e.target.checked })}
                      className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <span>Target DIY Builders (Wix, Weebly, GoDaddy, Squarespace)</span>
                  </label>
                </div>

                {/* 4. Lead Discovery Sources */}
                <div className="pt-3 border-t border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                      Discovery Data Sources:
                    </span>
                    <span className="text-[10px] text-emerald-400 font-semibold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800">
                      Multi-Source
                    </span>
                  </div>

                  {/* The Roofing List (theroofinglist.com) */}
                  <label className="flex items-start space-x-2.5 p-2 rounded-xl border border-blue-900/60 bg-blue-950/20 cursor-pointer hover:bg-blue-950/30 transition">
                    <input
                      type="checkbox"
                      checked={discoveryProviders.the_roofing_list}
                      onChange={(e) => setDiscoveryProviders({ ...discoveryProviders, the_roofing_list: e.target.checked })}
                      className="mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-bold text-white">The Roofing List</span>
                        <span className="text-[9px] bg-blue-500/20 text-blue-300 font-bold px-1.5 py-0.2 rounded border border-blue-500/30">
                          theroofinglist.com
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        US verified roofing directory. Multi-page pagination + company website validation.
                      </p>
                    </div>
                  </label>

                  {/* OpenStreetMap */}
                  <label className="flex items-start space-x-2.5 p-2 rounded-xl border border-slate-800 bg-slate-950/40 cursor-pointer hover:bg-slate-900 transition">
                    <input
                      type="checkbox"
                      checked={discoveryProviders.openstreetmap}
                      onChange={(e) => setDiscoveryProviders({ ...discoveryProviders, openstreetmap: e.target.checked })}
                      className="mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-bold text-slate-200">OpenStreetMap Overpass</span>
                        <span className="text-[9px] text-emerald-400 font-semibold">Public Free</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        Geographic business tags, point coordinates, and postal addresses.
                      </p>
                    </div>
                  </label>

                  {/* Public Search Engines */}
                  <label className="flex items-start space-x-2.5 p-2 rounded-xl border border-slate-800 bg-slate-950/40 cursor-pointer hover:bg-slate-900 transition">
                    <input
                      type="checkbox"
                      checked={discoveryProviders.search_engines}
                      onChange={(e) => setDiscoveryProviders({ ...discoveryProviders, search_engines: e.target.checked })}
                      className="mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-bold text-slate-200">Public Search Engines</span>
                        <span className="text-[9px] text-slate-500">DuckDuckGo / Bing</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        Deep web searches for company websites and snippet contact lines.
                      </p>
                    </div>
                  </label>

                  {/* Google Places */}
                  <label className="flex items-start space-x-2.5 p-2 rounded-xl border border-slate-800 bg-slate-950/40 cursor-pointer hover:bg-slate-900 transition">
                    <input
                      type="checkbox"
                      checked={discoveryProviders.google_places}
                      onChange={(e) => setDiscoveryProviders({ ...discoveryProviders, google_places: e.target.checked })}
                      className="mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-bold text-slate-200">Google Places API</span>
                        <span className="text-[9px] text-slate-500">Optional API Key</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        Local maps POI records, direct phones, and star ratings.
                      </p>
                    </div>
                  </label>
                </div>

                {/* 5. Action Buttons */}
                <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
                  <button
                    onClick={handleStartAutomation}
                    disabled={activeAutomation && activeAutomation.status === "RUNNING"}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 transition disabled:opacity-50 flex items-center justify-center space-x-2"
                  >
                    <span>⚡ START AUTOMATED SEARCH</span>
                  </button>

                  {activeAutomation && (
                    <div className="flex items-center space-x-2">
                      {activeAutomation.status === "RUNNING" ? (
                        <button
                          onClick={handlePauseAutomation}
                          className="flex-1 py-2 px-3 bg-amber-600/30 hover:bg-amber-600/40 text-amber-300 border border-amber-600/50 rounded-xl text-xs font-semibold transition"
                        >
                          ⏸ Pause
                        </button>
                      ) : activeAutomation.status === "PAUSED" ? (
                        <button
                          onClick={handleResumeAutomation}
                          className="flex-1 py-2 px-3 bg-emerald-600/30 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-600/50 rounded-xl text-xs font-semibold transition"
                        >
                          ▶ Resume
                        </button>
                      ) : null}

                      {(activeAutomation.status === "RUNNING" || activeAutomation.status === "PAUSED") && (
                        <button
                          onClick={handleStopAutomation}
                          className="flex-1 py-2 px-3 bg-rose-600/30 hover:bg-rose-600/40 text-rose-300 border border-rose-600/50 rounded-xl text-xs font-semibold transition"
                        >
                          ⏹ Stop
                        </button>
                      )}

                      {activeAutomation.failed_count > 0 && (
                        <button
                          onClick={handleRetryFailed}
                          className="flex-1 py-2 px-3 bg-indigo-600/30 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-600/50 rounded-xl text-xs font-semibold transition"
                        >
                          🔄 Retry Failed ({activeAutomation.failed_count})
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Live Monitor & Discovered Leads Table */}
            <div className="lg:col-span-7 space-y-6">
              {/* Active Automation Progress Monitor */}
              {activeAutomation ? (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          Active Search Session:
                        </span>
                        <span className="text-xs text-white font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                          {activeAutomation.id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        {activeAutomation.search_config?.industries?.join(", ")} in{" "}
                        {activeAutomation.search_config?.states?.join(", ")} ({activeAutomation.search_config?.radius_miles}mi radius)
                      </p>
                    </div>

                    {/* Export Actions for this Automation */}
                    <div className="flex items-center space-x-2">
                      <a
                        href={`/api/export/automation/${activeAutomation.id}/excel`}
                        download
                        className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1.5 shadow-sm"
                      >
                        <span>📗 Export 6-Sheet Excel</span>
                      </a>
                      <a
                        href={`/api/export/automation/${activeAutomation.id}/csv`}
                        download
                        className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
                      >
                        📄 CSV
                      </a>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-semibold text-slate-300">
                        Automation Completion: {activeAutomation.progress_percentage || 0}%
                      </span>
                      <span className="text-slate-400 font-mono">
                        {activeAutomation.enriched_count || 0} / {activeAutomation.target_leads || 0} Leads Enriched
                      </span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800">
                      <div
                        className="bg-gradient-to-r from-blue-600 to-indigo-500 h-full rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${Math.min(activeAutomation.progress_percentage || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Live KPI Metric Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                      <div className="text-xl font-black text-blue-400">
                        {activeAutomation.discovered_count || 0}
                      </div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mt-0.5">
                        Discovered
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                      <div className="text-xl font-black text-emerald-400">
                        {activeAutomation.decision_makers_found || 0}
                      </div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mt-0.5">
                        Decision Makers
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                      <div className="text-xl font-black text-cyan-400">
                        {activeAutomation.verified_emails_found || 0}
                      </div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mt-0.5">
                        Verified Emails
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                      <div className="text-xl font-black text-amber-400">
                        {activeAutomation.redesign_opps_count || 0}
                      </div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mt-0.5">
                        Redesign Opps
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto text-xl">
                    🚀
                  </div>
                  <h4 className="text-base font-bold text-white">No Active Automation Running</h4>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Select your target US state, cities, and trades on the left, then click <strong>START AUTOMATED SEARCH</strong> to initiate autonomous discovery and 12-field enrichment.
                  </p>
                </div>
              )}

              {/* Discovered Leads Table */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-white">
                      📋 Discovered & Enriched Leads ({totalAutomationLeads})
                    </h3>
                  </div>

                  {/* Score & Redesign Filters */}
                  <div className="flex items-center space-x-2">
                    <select
                      value={automationFilterMinScore}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setAutomationFilterMinScore(val);
                        if (activeAutomationId) {
                          loadAutomationLeads(activeAutomationId, 1);
                        }
                      }}
                      className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none"
                    >
                      <option value={0}>All Scores (0-100)</option>
                      <option value={40}>Min Score 40+</option>
                      <option value={60}>Min Score 60+</option>
                      <option value={75}>High Priority (75+)</option>
                    </select>

                    <button
                      onClick={() => {
                        const next = !automationFilterRedesignOnly;
                        setAutomationFilterRedesignOnly(next);
                        if (activeAutomationId) {
                          loadAutomationLeads(activeAutomationId, 1);
                        }
                      }}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                        automationFilterRedesignOnly
                          ? "bg-amber-600/30 border-amber-500 text-amber-200"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      🎨 Redesign Opps
                    </button>
                  </div>
                </div>

                {/* Floating Bulk CRM & Action Bar */}
                {selectedLeadIds.length > 0 && (
                  <div className="bg-gradient-to-r from-blue-950 via-indigo-950 to-slate-900 border border-blue-600/80 p-3 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-xl animate-in fade-in">
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-white bg-blue-600 px-2.5 py-0.5 rounded-full text-xs">
                        {selectedLeadIds.length}
                      </span>
                      <span className="text-blue-200 font-semibold">prospects selected</span>
                    </div>
                    <div className="flex items-center flex-wrap gap-2">
                      <select
                        onChange={(e) => {
                          if (e.target.value) handleBulkStatus(e.target.value);
                          e.target.value = "";
                        }}
                        className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none"
                      >
                        <option value="">-- Bulk Set Pipeline Status --</option>
                        <option value="New">Set: New Prospect</option>
                        <option value="Pitched">Set: Pitched</option>
                        <option value="Contacted">Set: Contacted</option>
                        <option value="Replied">Set: Replied</option>
                        <option value="Meeting Booked">Set: Meeting Booked</option>
                        <option value="Closed">Set: Closed / Won</option>
                        <option value="Not Interested">Set: Not Interested</option>
                      </select>
                      <button
                        onClick={handleBulkWebhookPush}
                        className="px-3 py-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-lg font-bold flex items-center space-x-1 shadow-sm"
                      >
                        <span>🚀 Push to Webhook / CRM</span>
                      </button>
                      <button
                        onClick={() => setSelectedLeadIds([])}
                        className="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-lg hover:text-white"
                      >
                        Deselect
                      </button>
                    </div>
                  </div>
                )}

                {/* Table */}
                <div className="overflow-x-auto custom-scrollbar">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                        <th className="py-2.5 px-3 w-8">
                          <input
                            type="checkbox"
                            checked={automationLeads.length > 0 && selectedLeadIds.length === automationLeads.length}
                            onChange={handleSelectAllLeads}
                            className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                          />
                        </th>
                        <th className="py-2.5 px-2 w-8 text-center">★</th>
                        <th className="py-2.5 px-3">Company</th>
                        <th className="py-2.5 px-3">Location</th>
                        <th className="py-2.5 px-3">Lead Score</th>
                        <th className="py-2.5 px-3">Sales Pipeline</th>
                        <th className="py-2.5 px-3">Decision Maker</th>
                        <th className="py-2.5 px-3">Contact Info</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {automationLeads.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="py-8 text-center text-slate-500">
                            {activeAutomationId ? "No leads matching criteria yet." : "Start an automation session to discover leads."}
                          </td>
                        </tr>
                      ) : (
                        automationLeads.map((company) => {
                          const primaryDM = company.owner_name || company.ceo_name || company.founder_name;
                          const primaryDMTitle = company.owner_name ? "Owner" : company.ceo_name ? "CEO" : "Founder";

                          return (
                            <tr key={company.id} className="hover:bg-slate-800/40 transition">
                              <td className="py-3 px-3">
                                <input
                                  type="checkbox"
                                  checked={selectedLeadIds.includes(company.id)}
                                  onChange={() => handleToggleSelectLead(company.id)}
                                  className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                                />
                              </td>

                              <td className="py-3 px-2 text-center">
                                <button
                                  onClick={() => handleToggleStar(company.id)}
                                  className={`text-base font-bold transition ${
                                    company.is_starred ? "text-amber-400 scale-110" : "text-slate-600 hover:text-slate-400"
                                  }`}
                                  title={company.is_starred ? "Starred Prospect" : "Star Prospect"}
                                >
                                  {company.is_starred ? "★" : "☆"}
                                </button>
                              </td>

                              <td className="py-3 px-3">
                                <div className="font-bold text-white text-xs">{company.name}</div>
                                <div className="text-[11px] text-slate-400 truncate max-w-[190px]">
                                  {(company.website && company.website !== "N/A") || (company.website_url && company.website_url !== "N/A") ? (
                                    <a
                                      href={(company.website || company.website_url).startsWith("http") ? (company.website || company.website_url) : `https://${company.website || company.website_url}`}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-blue-400 hover:underline"
                                    >
                                      {(company.website || company.website_url).replace(/^https?:\/\/(www\.)?/, "")}
                                    </a>
                                  ) : (
                                    <span className="text-rose-400 font-semibold text-[10px]">No Verified Website</span>
                                  )}
                                </div>
                                {company.directory_profile_url && (
                                  <div className="mt-0.5">
                                    <a
                                      href={company.directory_profile_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-[10px] text-indigo-400 hover:underline flex items-center space-x-1"
                                    >
                                      <span>The Roofing List Profile ↗</span>
                                    </a>
                                  </div>
                                )}
                              </td>

                              <td className="py-3 px-3">
                                <div className="text-slate-200">
                                  {company.city}, {company.state}
                                </div>
                                {company.distance_from_center_miles != null && (
                                  <div className="text-[10px] text-slate-500">
                                    {company.distance_from_center_miles.toFixed(1)} mi away
                                  </div>
                                )}
                              </td>

                              <td className="py-3 px-3">
                                {renderScoreBadge(company.lead_score || 0, company.lead_score_reason)}
                              </td>

                              <td className="py-3 px-3">
                                <select
                                  value={company.lead_status || "New"}
                                  onChange={(e) => handleUpdateLeadStatus(company.id, e.target.value)}
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold border focus:outline-none cursor-pointer ${
                                    company.lead_status === "Meeting Booked" || company.lead_status === "Closed"
                                      ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                                      : company.lead_status === "Pitched" || company.lead_status === "Replied"
                                      ? "bg-purple-950 text-purple-300 border-purple-800"
                                      : company.lead_status === "Contacted"
                                      ? "bg-blue-950 text-blue-300 border-blue-800"
                                      : "bg-slate-950 text-slate-400 border-slate-800"
                                  }`}
                                >
                                  <option value="New">New</option>
                                  <option value="Contacted">Contacted</option>
                                  <option value="Pitched">Pitched</option>
                                  <option value="Replied">Replied</option>
                                  <option value="Meeting Booked">Meeting Booked</option>
                                  <option value="Closed">Closed / Won</option>
                                  <option value="Not Interested">Not Interested</option>
                                </select>
                              </td>

                              <td className="py-3 px-3">
                                {primaryDM ? (
                                  <div>
                                    <div className="font-semibold text-slate-200">{primaryDM}</div>
                                    <div className="text-[10px] text-blue-400">{primaryDMTitle}</div>
                                  </div>
                                ) : (
                                  <span className="text-slate-500 text-[11px]">Searching...</span>
                                )}
                              </td>

                              <td className="py-3 px-3 space-y-0.5">
                                {company.business_email ? (
                                  <div className="text-emerald-300 font-mono text-[11px] truncate max-w-[150px]">
                                    ✉ {company.business_email}
                                  </div>
                                ) : null}
                                {company.business_phone ? (
                                  <div className="text-slate-300 text-[11px]">
                                    ☎ {company.business_phone}
                                  </div>
                                ) : null}
                                {!company.business_email && !company.business_phone && (
                                  <span className="text-slate-500 text-[11px]">—</span>
                                )}
                              </td>

                              <td className="py-3 px-3 text-right">
                                <button
                                  onClick={() => handleOpenCompanyDetail(company.id)}
                                  className="px-2.5 py-1 bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white rounded text-[11px] font-semibold transition"
                                >
                                  View Intelligence
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalAutomationLeads > 20 && (
                  <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
                    <span className="text-slate-400">
                      Showing Page {automationLeadsPage} of {Math.ceil(totalAutomationLeads / 20)}
                    </span>
                    <div className="flex items-center space-x-1">
                      <button
                        disabled={automationLeadsPage <= 1}
                        onClick={() => {
                          const p = automationLeadsPage - 1;
                          loadAutomationLeads(activeAutomationId, p);
                        }}
                        className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded disabled:opacity-40"
                      >
                        Prev
                      </button>
                      <button
                        disabled={automationLeadsPage >= Math.ceil(totalAutomationLeads / 20)}
                        onClick={() => {
                          const p = automationLeadsPage + 1;
                          loadAutomationLeads(activeAutomationId, p);
                        }}
                        className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded disabled:opacity-40"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: AUTOMATION HISTORY                                     */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "history" && (
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Automation Execution History</h2>
              <p className="text-xs text-slate-400">
                Audit log of all autonomous lead generation runs with performance metrics and direct downloads.
              </p>
            </div>
            <button
              onClick={loadAutomationHistory}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
            >
              🔄 Refresh History
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-950/60">
                  <th className="py-3 px-4">Session ID</th>
                  <th className="py-3 px-4">Location & Radius</th>
                  <th className="py-3 px-4">Target Industry</th>
                  <th className="py-3 px-4">Progress / Enriched</th>
                  <th className="py-3 px-4">Decision Makers</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {automationHistory.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No automation history found. Start your first search in Automated Lead Generation.
                    </td>
                  </tr>
                ) : (
                  automationHistory.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {item.id}
                        <div className="text-[10px] text-slate-500">
                          {new Date(item.created_at).toLocaleString()}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">
                          {item.search_config?.states?.join(", ")}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {item.search_config?.cities?.length > 0
                            ? item.search_config.cities.slice(0, 3).join(", ")
                            : "Entire State"}{" "}
                          ({item.search_config?.radius_miles}mi)
                        </div>
                      </td>

                      <td className="py-3 px-4 text-slate-300">
                        {item.search_config?.industries?.join(", ")}
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">
                          {item.enriched_count} / {item.target_leads}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {item.progress_percentage}% completed
                        </div>
                      </td>

                      <td className="py-3 px-4 text-emerald-400 font-bold">
                        {item.decision_makers_found}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.status === "COMPLETED"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : item.status === "RUNNING"
                              ? "bg-blue-950 text-blue-300 border border-blue-800 animate-pulse"
                              : item.status === "PAUSED"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : "bg-rose-950 text-rose-300 border border-rose-800"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right space-x-2">
                        <button
                          onClick={() => {
                            setActiveAutomationId(item.id);
                            setActiveAutomation(item);
                            setActiveTab("automation");
                            loadAutomationLeads(item.id, 1);
                          }}
                          className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold"
                        >
                          View Leads
                        </button>
                        <a
                          href={`/api/export/automation/${item.id}/excel`}
                          download
                          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px]"
                        >
                          📗 Excel
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: ORIGINAL LEAD ENRICHMENT (EXCEL/CSV UPLOAD FLOW)       */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "enrichment" && (
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-white">Manual Lead Enrichment & Upload</h2>
              <p className="text-xs text-slate-400">
                Upload existing CSV/XLSX lists, map columns with preview confirmation, and execute 12-field research.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setUploadModalOpen(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-sm"
              >
                📁 Upload Excel / CSV
              </button>
              {currentJob && (
                <a
                  href={`/api/export/job/${currentJob.id}/excel`}
                  download
                  className="px-3 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition"
                >
                  📗 Download Excel
                </a>
              )}
            </div>
          </div>

          {/* Job Overview Strip */}
          {currentJob && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 font-mono">Job: {currentJob.id}</span>
                <div className="font-bold text-white text-sm">
                  {currentJob.filename} &bull; {currentJob.total_companies} Companies
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-xs font-bold text-slate-300">
                    {currentJob.processed_companies} / {currentJob.total_companies} Processed
                  </div>
                  <div className="text-[10px] text-slate-500">Status: {currentJob.status}</div>
                </div>
              </div>
            </div>
          )}

          {/* Lead Table for Job */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-white mb-3">Enriched Companies</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                    <th className="py-2 px-3">Company</th>
                    <th className="py-2 px-3">Location</th>
                    <th className="py-2 px-3">Owner/CEO</th>
                    <th className="py-2 px-3">Email</th>
                    <th className="py-2 px-3">Phone</th>
                    <th className="py-2 px-3 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {companies.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No companies in this job or no job selected.
                      </td>
                    </tr>
                  ) : (
                    companies.map(c => (
                      <tr key={c.id} className="hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-semibold text-white">{c.name}</td>
                        <td className="py-2.5 px-3 text-slate-300">{c.city}, {c.state}</td>
                        <td className="py-2.5 px-3 text-slate-300">{c.owner_name || c.ceo_name || "—"}</td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">{c.business_email || "—"}</td>
                        <td className="py-2.5 px-3 text-slate-300">{c.business_phone || "—"}</td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleOpenCompanyDetail(c.id)}
                            className="px-2 py-1 bg-slate-800 hover:bg-blue-600 rounded text-[11px]"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 4: GENERAL DASHBOARD                                      */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "dashboard" && (
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-xl font-bold text-white">System Dashboard</h2>
            <p className="text-xs text-slate-400 mt-1">
              Real-time analytics across all automated and manual lead enrichment pipelines.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="text-slate-400 text-xs font-semibold uppercase">Total Automated Runs</div>
              <div className="text-3xl font-black text-white mt-1">{automationHistory.length}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="text-slate-400 text-xs font-semibold uppercase">Active Modules</div>
              <div className="text-3xl font-black text-blue-400 mt-1">2 Engines</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="text-slate-400 text-xs font-semibold uppercase">US Census Coverage</div>
              <div className="text-3xl font-black text-emerald-400 mt-1">50 States + DC</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="text-slate-400 text-xs font-semibold uppercase">Target Agency</div>
              <div className="text-sm font-bold text-white mt-2">Tex Web Solutions</div>
            </div>
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL: EXCEL PREVIEW & MAPPING MODAL                          */}
      {/* ------------------------------------------------------------- */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Upload Excel / CSV Lead File</h3>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {!previewData ? (
              <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-2xl p-8 text-center cursor-pointer transition">
                <input
                  type="file"
                  accept=".xlsx,.csv"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="modalFileInput"
                />
                <label htmlFor="modalFileInput" className="cursor-pointer space-y-2 block">
                  <div className="text-3xl">📁</div>
                  <div className="text-sm font-bold text-white">
                    {uploadLoading ? "Reading File..." : "Click to select XLSX or CSV file"}
                  </div>
                  <div className="text-xs text-slate-400">
                    Supports original columns: id, name, trades, city, state, phone, webssite url, claimed
                  </div>
                </label>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-xs text-emerald-400 font-semibold">
                  ✓ File loaded: {previewData.filename} ({previewData.total_rows} companies detected)
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-bold text-white">Verify Column Mapping:</div>
                  <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
                    {[
                      { key: "id", label: "Lead ID" },
                      { key: "name", label: "Company Name" },
                      { key: "trades", label: "Trades / Industry" },
                      { key: "city", label: "City" },
                      { key: "state", label: "State" },
                      { key: "phone", label: "Phone" },
                      { key: "website_url", label: "Website URL" },
                      { key: "claimed", label: "Claimed Status" }
                    ].map((col) => (
                      <div key={col.key} className="flex items-center justify-between">
                        <span className="text-slate-400 font-semibold">{col.label}:</span>
                        <select
                          value={columnMappings[col.key] || (col.key === "website_url" ? columnMappings["webssite url"] : "") || ""}
                          onChange={(e) => {
                            const newMaps = { ...columnMappings, [col.key]: e.target.value };
                            if (col.key === "website_url") {
                              newMaps["webssite url"] = e.target.value;
                            }
                            setColumnMappings(newMaps);
                          }}
                          className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs max-w-[150px] truncate"
                        >
                          <option value="">-- Auto/None --</option>
                          {(previewData.original_headers || previewData.headers || []).map((h) => (
                            <option key={h} value={h}>{h}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    onClick={() => setPreviewData(null)}
                    className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded text-xs"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleConfirmMappingAndStart}
                    disabled={uploadLoading}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold"
                  >
                    {uploadLoading ? "Starting..." : "Confirm & Start 12-Field Research"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* DRAWER: 12-FIELD INTELLIGENCE DRAWER                          */}
      {/* ------------------------------------------------------------- */}
      {selectedCompanyId && companyDetail && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-slate-900 border-l border-slate-800 w-full max-w-2xl h-full flex flex-col p-6 space-y-4 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white">{companyDetail.name}</h3>
                <p className="text-xs text-slate-400">
                  {companyDetail.city}, {companyDetail.state} &bull; {companyDetail.trades}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedCompanyId(null);
                  setCompanyDetail(null);
                }}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {/* Tab navigation in drawer */}
            <div className="flex items-center space-x-1 border-b border-slate-800 pb-2 text-xs">
              <button
                onClick={() => setDrawerTab("mandatory")}
                className={`px-3 py-1.5 rounded-lg font-semibold ${
                  drawerTab === "mandatory" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
                }`}
              >
                Mandatory 12 Fields
              </button>
              <button
                onClick={() => setDrawerTab("pitch")}
                className={`px-3 py-1.5 rounded-lg font-semibold ${
                  drawerTab === "pitch" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
                }`}
              >
                Personalized Pitch
              </button>
              <button
                onClick={() => setDrawerTab("audit")}
                className={`px-3 py-1.5 rounded-lg font-semibold ${
                  drawerTab === "audit" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
                }`}
              >
                Website Redesign Audit
              </button>
            </div>

            {/* TAB: MANDATORY 12 FIELDS */}
            {drawerTab === "mandatory" && (
              <div className="space-y-4 text-xs">
                {/* 1-4 Decision Makers */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <h4 className="font-bold text-blue-400 uppercase tracking-wider text-[11px]">
                    Decision-Maker Intelligence (Owner / CEO / Founder)
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400">1. Owner:</span>{" "}
                      <span className="font-semibold text-white">{companyDetail.owner_name || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">2. CEO:</span>{" "}
                      <span className="font-semibold text-white">{companyDetail.ceo_name || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">3. Founder:</span>{" "}
                      <span className="font-semibold text-white">{companyDetail.founder_name || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">4. Co-Founder:</span>{" "}
                      <span className="font-semibold text-white">{companyDetail.co_founder_name || "Not Found"}</span>
                    </div>
                  </div>
                </div>

                {/* 5-8 Contact Info */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">
                    Direct Contact Channels
                  </h4>
                  <div className="space-y-1.5">
                    <div>
                      <span className="text-slate-400">5. Business Email:</span>{" "}
                      <span className="font-mono text-emerald-300">{companyDetail.business_email || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">6. Business Phone:</span>{" "}
                      <span className="text-slate-200">{companyDetail.business_phone || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">7. Personal Email:</span>{" "}
                      <span className="font-mono text-emerald-300">{companyDetail.personal_email || "Not Found"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">8. Personal Phone:</span>{" "}
                      <span className="text-slate-200">{companyDetail.personal_phone || "Not Found"}</span>
                    </div>
                  </div>
                </div>

                {/* 9-12 Social Profiles */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <h4 className="font-bold text-cyan-400 uppercase tracking-wider text-[11px]">
                    Social & Professional Profiles
                  </h4>
                  <div className="space-y-1.5">
                    <div>
                      <span className="text-slate-400">9. Personal LinkedIn:</span>{" "}
                      {companyDetail.personal_linkedin ? (
                        <a href={companyDetail.personal_linkedin} target="_blank" rel="noreferrer" className="text-blue-400 underline">
                          {companyDetail.personal_linkedin}
                        </a>
                      ) : "Not Found"}
                    </div>
                    <div>
                      <span className="text-slate-400">10. Business LinkedIn:</span>{" "}
                      {companyDetail.business_linkedin ? (
                        <a href={companyDetail.business_linkedin} target="_blank" rel="noreferrer" className="text-blue-400 underline">
                          {companyDetail.business_linkedin}
                        </a>
                      ) : "Not Found"}
                    </div>
                    <div>
                      <span className="text-slate-400">11. Business Instagram:</span>{" "}
                      {companyDetail.business_instagram ? (
                        <a href={companyDetail.business_instagram} target="_blank" rel="noreferrer" className="text-pink-400 underline">
                          {companyDetail.business_instagram}
                        </a>
                      ) : "Not Found"}
                    </div>
                    <div>
                      <span className="text-slate-400">12. Business Facebook:</span>{" "}
                      {companyDetail.business_facebook ? (
                        <a href={companyDetail.business_facebook} target="_blank" rel="noreferrer" className="text-blue-300 underline">
                          {companyDetail.business_facebook}
                        </a>
                      ) : "Not Found"}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: PERSONALIZED PITCH */}
            {drawerTab === "pitch" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Outreach Email Pitch for Tex Web Solutions:</span>
                  <button
                    onClick={() => copyPitchToClipboard(companyDetail.custom_pitch)}
                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold"
                  >
                    {pitchCopied ? "✓ Copied!" : "📋 Copy Pitch"}
                  </button>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans">
                  {companyDetail.custom_pitch || "No pitch generated for this company."}
                </div>
              </div>
            )}

            {/* TAB: AUDIT */}
            {drawerTab === "audit" && (
              <div className="space-y-3 text-xs">
                {/* Live Website Visual Proof Screenshot */}
                {companyDetail.website_screenshot_url || (companyDetail.official_website && companyDetail.official_website !== "N/A") ? (
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200">📸 Live Website Visual Proof:</span>
                      {companyDetail.official_website && companyDetail.official_website !== "N/A" && (
                        <a
                          href={companyDetail.official_website.startsWith("http") ? companyDetail.official_website : `https://${companyDetail.official_website}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-400 text-[11px] hover:underline"
                        >
                          Open Website ↗
                        </a>
                      )}
                    </div>
                    <div className="rounded-lg overflow-hidden border border-slate-800 max-h-56 bg-slate-900 flex items-center justify-center">
                      <img
                        src={companyDetail.website_screenshot_url || `https://s0.wp.com/mshots/v1/${companyDetail.official_website.startsWith("http") ? companyDetail.official_website : "https://" + companyDetail.official_website}?w=800&h=600`}
                        alt="Current Website Visual Proof"
                        className="w-full object-cover object-top hover:scale-105 transition duration-300"
                        onError={(e) => { e.target.parentElement.innerHTML = '<div class="py-6 text-slate-500 text-center text-xs">Website preview offline or blocked</div>'; }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-950 p-4 rounded-xl border border-amber-900/40 text-amber-300 text-xs flex items-center space-x-2">
                    <span>⚠️ No website detected — 100% Greenfield Web Development sale opportunity for Tex Web Solutions!</span>
                  </div>
                )}

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <h4 className="font-bold text-amber-400 uppercase tracking-wider text-[11px]">Tex Web Solutions Agency Audit</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <div><span className="text-slate-400">CMS Framework:</span> <span className="font-semibold text-white">{companyDetail.tech_stack_cms || companyDetail.cms_framework || "None / Custom"}</span></div>
                    <div><span className="text-slate-400">Opportunity Score:</span> <span className="font-semibold text-white">{companyDetail.lead_score || 0}/100</span></div>
                    <div><span className="text-slate-400">SSL Encryption:</span> <span className={companyDetail.has_ssl ? "text-emerald-400" : "text-rose-400"}>{companyDetail.has_ssl ? "Yes (Secured)" : "No (Insecure HTTP)"}</span></div>
                    <div><span className="text-slate-400">Mobile Responsive:</span> <span className={companyDetail.is_mobile_responsive ? "text-emerald-400" : "text-amber-400"}>{companyDetail.is_mobile_responsive ? "Yes" : "Needs Optimization"}</span></div>
                  </div>
                  <div><span className="text-slate-400">Audit Diagnosis:</span> <span className="text-slate-300">{companyDetail.lead_score_reason || "Evaluated for redesign opportunities"}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL: API SETTINGS                                           */}
      {/* ------------------------------------------------------------- */}
      {apiModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">API Integrations & Outreach Channels</h3>
              <button onClick={() => setApiModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {/* Outgoing Webhook Push for CRM */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-indigo-900/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-xs">CRM Outgoing Webhook (Zapier / Make / n8n / HubSpot)</span>
                <span className="text-[10px] text-indigo-400 font-semibold">Active Push</span>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="https://hooks.zapier.com/hooks/catch/... or n8n webhook"
                  value={webhookUrl}
                  onChange={(e) => {
                    setWebhookUrl(e.target.value);
                    localStorage.setItem("saved_webhook_url", e.target.value);
                  }}
                  className="flex-1 bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                />
                <button
                  onClick={() => {
                    localStorage.setItem("saved_webhook_url", webhookUrl);
                    alert("Webhook URL saved to browser storage!");
                  }}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold"
                >
                  Save Webhook
                </button>
              </div>
              <p className="text-[10px] text-slate-500">
                Pushes selected qualified prospects directly into your sales CRM or email outreach sequence.
              </p>
            </div>

            {/* HTTP/SOCKS5 Proxy Rotation */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-xs">Residential Proxy Rotation (Anti-Bot Bypass)</span>
                <span className="text-[10px] text-slate-500">Optional</span>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="http://user:pass@gate.smartproxy.com:7000 or BrightData"
                  value={proxyUrl}
                  onChange={(e) => {
                    setProxyUrl(e.target.value);
                    localStorage.setItem("saved_proxy_url", e.target.value);
                  }}
                  className="flex-1 bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                />
                <button
                  onClick={() => {
                    localStorage.setItem("saved_proxy_url", proxyUrl);
                    alert("Proxy settings saved!");
                  }}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-semibold"
                >
                  Save Proxy
                </button>
              </div>
              <p className="text-[10px] text-slate-500">
                Routes high-volume scraping requests through rotating US IP proxies to prevent rate limits.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                Data & Enrichment API Keys:
              </span>
              {apiConfigs.map((cfg) => (
                <div key={cfg.provider_name} className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-xs">{cfg.provider_name}</span>
                    <span className={`w-2 h-2 rounded-full ${cfg.is_connected ? "bg-emerald-500" : cfg.has_key ? "bg-amber-500" : "bg-slate-600"}`}></span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      placeholder={`Enter ${cfg.provider_name} Key`}
                      defaultValue={cfg.has_key ? "••••••••••••••••" : ""}
                      id={`key_${cfg.provider_name}`}
                      className="flex-1 bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                    />
                    <button
                      onClick={() => {
                        const val = document.getElementById(`key_${cfg.provider_name}`).value;
                        if (val && !val.includes("•")) {
                          handleSaveApiKey(cfg.provider_name, val);
                        }
                      }}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold"
                    >
                      Save
                    </button>
                    <button
                      disabled={testingProvider === cfg.provider_name}
                      onClick={() => {
                        const val = document.getElementById(`key_${cfg.provider_name}`).value;
                        handleTestApi(cfg.provider_name, val.includes("•") ? "" : val);
                      }}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
                    >
                      {testingProvider === cfg.provider_name ? "Testing..." : "Test"}
                    </button>
                  </div>
                  {testResult[cfg.provider_name] && (
                    <p className={`text-[11px] ${testResult[cfg.provider_name].success ? "text-emerald-400" : "text-rose-400"}`}>
                      {testResult[cfg.provider_name].message}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
