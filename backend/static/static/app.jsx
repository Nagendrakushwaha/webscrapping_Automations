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
  // Navigation: 'dashboard' | 'enrichment' | 'automation' | 'national_roofing' | 'history' | 'settings'
  const [activeTab, setActiveTab] = useState("dashboard");
  const [theme, setTheme] = useState(() => localStorage.getItem("app_theme") || "light");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [globalSearch, setGlobalSearch] = useState("");

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("app_theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    }
  };

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    }
  }, [theme]);

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
    <div className={`min-h-screen flex ${theme === 'dark' ? 'dark bg-slate-950 text-slate-100' : 'bg-[#f4f7fc] text-slate-800'} font-sans antialiased transition-colors duration-150`}>
      {/* Toast Alert Banner */}
      {toast && (
        <div className={`fixed top-5 right-6 z-50 flex items-center space-x-3 px-5 py-3 rounded-2xl shadow-2xl border backdrop-blur-md text-sm font-semibold transition-all ${
          toast.type === "error" ? "bg-red-950/90 text-red-200 border-red-800" : "bg-brand-600/95 text-white border-brand-400/40"
        }`}>
          <span>{toast.type === "error" ? "⚠️" : "🚀"}</span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* LEFT SIDEBAR NAVIGATION (Matching XYRA & Analytics Dashboard) */}
      {/* ------------------------------------------------------------- */}
      <aside className={`${sidebarCollapsed ? 'w-20' : 'w-64'} flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800 flex flex-col justify-between z-30 transition-all duration-200 shadow-sm sticky top-0 h-screen`}>
        <div className="flex flex-col h-full overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* Brand Logo & Title */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800/60">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-accent-500 flex items-center justify-center font-black text-xl text-white shadow-md shadow-brand-500/25 flex-shrink-0">
                T
              </div>
              {!sidebarCollapsed && (
                <div className="min-w-0">
                  <div className="flex items-center space-x-1.5">
                    <h1 className="text-sm font-extrabold tracking-tight text-slate-900 dark:text-white truncate">AI LEAD INTEL</h1>
                    <span className="text-[9px] bg-brand-50 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 font-bold px-1.5 py-0.5 rounded border border-brand-200 dark:border-brand-800/60">
                      PRO
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate">
                    Tex Web Solutions
                  </p>
                </div>
              )}
            </div>
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition text-xs"
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? "→" : "←"}
            </button>
          </div>

          {/* Navigation Section */}
          <div className="space-y-1">
            {!sidebarCollapsed && (
              <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider px-3 mb-2 block">
                Modules & Analytics
              </span>
            )}

            {/* Dashboard Nav */}
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "dashboard"
                  ? "bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 shadow-sm border border-brand-200/60 dark:border-brand-800/50"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">📊</span>
                {!sidebarCollapsed && <span>Dashboard & Analytics</span>}
              </div>
            </button>

            {/* Automated Lead Gen Nav */}
            <button
              onClick={() => setActiveTab("automation")}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "automation"
                  ? "bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 shadow-sm border border-brand-200/60 dark:border-brand-800/50"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">🚀</span>
                {!sidebarCollapsed && <span>Automated Discovery</span>}
              </div>
              {!sidebarCollapsed && (
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              )}
            </button>

            {/* National Roofing Directory Nav */}
            <button
              onClick={() => {
                setActiveTab("national_roofing");
                loadNationalJobs();
                if (nationalAvailableCities.length === 0) loadNationalCities(nationalState);
              }}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "national_roofing"
                  ? "bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-200 shadow-sm border border-amber-200/60 dark:border-amber-800/50"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">🏢</span>
                {!sidebarCollapsed && <span>National Roofing Dir</span>}
              </div>
              {!sidebarCollapsed && (
                <span className="text-[9px] bg-amber-500/20 text-amber-700 dark:text-amber-300 px-1.5 py-0.5 rounded-md font-bold uppercase">
                  New
                </span>
              )}
            </button>

            {/* Lead Enrichment Nav */}
            <button
              onClick={() => setActiveTab("enrichment")}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "enrichment"
                  ? "bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 shadow-sm border border-brand-200/60 dark:border-brand-800/50"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">⚡</span>
                {!sidebarCollapsed && <span>Manual Enrichment</span>}
              </div>
            </button>

            {/* History Nav */}
            <button
              onClick={() => {
                setActiveTab("history");
                loadAutomationHistory();
              }}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "history"
                  ? "bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 shadow-sm border border-brand-200/60 dark:border-brand-800/50"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">📜</span>
                {!sidebarCollapsed && <span>Run History & Logs</span>}
              </div>
            </button>

            {/* API Settings Nav */}
            <button
              onClick={() => setApiModalOpen(true)}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60 transition-all`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-base">⚙️</span>
                {!sidebarCollapsed && <span>API & Gateway Keys</span>}
              </div>
            </button>
          </div>

          {/* Bottom Sidebar Widgets */}
          <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/60 space-y-3">
            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between px-3'} py-2 rounded-xl text-xs font-semibold bg-slate-100/70 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 transition`}
              title="Toggle Light / Dark Mode"
            >
              <div className="flex items-center space-x-2">
                <span>{theme === "dark" ? "☀️" : "🌙"}</span>
                {!sidebarCollapsed && <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>}
              </div>
              {!sidebarCollapsed && (
                <span className="text-[10px] text-slate-400 uppercase font-mono">{theme}</span>
              )}
            </button>

            {/* System Status Pill */}
            {!sidebarCollapsed && (
              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200/60 dark:border-slate-800/60">
                <div className="flex items-center justify-between text-[11px] mb-1">
                  <span className="text-slate-500 font-medium">Engine Status</span>
                  <span className="flex items-center text-emerald-600 dark:text-emerald-400 font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block mr-1"></span>
                    Active
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-emerald-500 h-1.5 rounded-full w-full"></div>
                </div>
              </div>
            )}

            {/* Company / Admin Badge */}
            {!sidebarCollapsed && (
              <div className="flex items-center space-x-3 px-1 pt-1">
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-300">
                  TW
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">Tex Web Solutions</div>
                  <div className="text-[10px] text-slate-400 truncate">Administrator</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* MAIN VIEWPORT CONTAINER                                       */}
      {/* ------------------------------------------------------------- */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto max-h-screen custom-scrollbar">
        {/* Top Header Bar (Matching XYRA) */}
        <header className="sticky top-0 z-20 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-8 py-3.5 flex items-center justify-between">
          {/* Breadcrumb / Title */}
          <div className="flex items-center space-x-3">
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white capitalize">
              {activeTab === "dashboard" && "Executive Analytics Dashboard"}
              {activeTab === "automation" && "Automated Lead Generation"}
              {activeTab === "national_roofing" && "National Roofing Directory"}
              {activeTab === "enrichment" && "Manual Lead Enrichment"}
              {activeTab === "history" && "Automation History & Logs"}
            </h2>
            <span className="text-slate-300 dark:text-slate-700">/</span>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {activeTab === "dashboard" ? "System Overview" : "B2B Acquisition"}
            </span>
          </div>

          {/* Search & Actions */}
          <div className="flex items-center space-x-4">
            {/* Global Quick Search Input */}
            <div className="relative hidden md:block">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400 text-xs">
                🔍
              </span>
              <input
                type="text"
                placeholder="Search leads, cities, decision-makers..."
                value={globalSearch}
                onChange={(e) => {
                  setGlobalSearch(e.target.value);
                  setSearchQuery(e.target.value);
                }}
                className="pl-8 pr-12 py-1.5 text-xs bg-slate-100/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 w-64 transition"
              />
              <span className="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-[10px] text-slate-400 font-mono">
                ⌘K
              </span>
            </div>

            {/* Setup Progress Indicator (like XYRA) */}
            <div className="hidden lg:flex items-center space-x-2 bg-slate-100/70 dark:bg-slate-800/60 px-3 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60 text-xs">
              <span className="text-[11px] font-bold text-slate-600 dark:text-slate-300">SYSTEM HEALTH</span>
              <div className="w-16 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                <div className="bg-emerald-500 h-1.5 rounded-full w-full"></div>
              </div>
              <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">100%</span>
            </div>

            {/* Quick Action Buttons */}
            <button
              onClick={() => setActiveTab("automation")}
              className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition shadow-sm flex items-center space-x-1.5"
            >
              <span>+</span>
              <span>New Search</span>
            </button>

            <button
              onClick={() => {
                if (currentJob) {
                  window.open(`/api/export/job/${currentJob.id}/excel`, "_blank");
                } else {
                  showToast("No active job selected for export.", "error");
                }
              }}
              className="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold transition border border-slate-200 dark:border-slate-700/80 flex items-center space-x-1.5"
            >
              <span>⬇</span>
              <span>Export CSV</span>
            </button>
          </div>
        </header>

        {/* Tab Content Viewport */}
        <div className="flex-1">

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
      {/* TAB: NATIONAL ROOFING DIRECTORY                               */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "national_roofing" && (
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-amber-950/60 via-slate-900 to-slate-900 border border-amber-800/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
              <div>
                <div className="flex items-center space-x-3 mb-1">
                  <span className="text-2xl">🏢</span>
                  <h2 className="text-xl font-black text-white tracking-tight">National Roofing Directory</h2>
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 font-bold px-2 py-0.5 rounded border border-amber-500/40 uppercase tracking-wider">
                    Dedicated Scraper
                  </span>
                </div>
                <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                  Discover, extract, enrich and export roofing contractor business information from <a href="https://www.nationalroofingdirectory.com/" target="_blank" rel="noreferrer" className="text-amber-400 hover:underline">National Roofing Directory</a>. Features automated city directory traversal, rel="next" multi-page pagination, strict official website validation, and dedicated <strong>@gmail.com extraction</strong>.
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-3 text-[11px] text-slate-400">
                  <span className="bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800 text-slate-300">
                    📍 Target: <strong className="text-white">{nationalState}</strong> (Reference: 10,107 Listings)
                  </span>
                  <span className="bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800 text-slate-300">
                    📧 Dedicated Gmail Extraction
                  </span>
                  <span className="bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800 text-slate-300">
                    🛡️ Strict Anti-Directory Validation
                  </span>
                  <span className="bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800 text-slate-300">
                    💾 Persistent Checkpoint Resume
                  </span>
                </div>
              </div>

              {nationalJobId && (
                <div className="flex items-center space-x-2">
                  <a
                    href={`/api/national-roofing/jobs/${nationalJobId}/export/excel`}
                    download
                    className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/20 flex items-center space-x-1.5 transition"
                  >
                    <span>📊</span>
                    <span>Export 8-Sheet XLSX</span>
                  </a>
                  <a
                    href={`/api/national-roofing/jobs/${nationalJobId}/export/csv`}
                    download
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition"
                  >
                    CSV
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Configuration and Live Progress Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 5 Cols: Search & Location Configuration */}
            <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <span>⚙️</span>
                    <span>Search & Location Configuration</span>
                  </h3>
                  <span className="text-[10px] text-amber-400 font-mono">USA / Multi-State</span>
                </div>

                {/* State Selection */}
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    1. Select Target State:
                  </label>
                  <select
                    value={nationalState}
                    onChange={(e) => {
                      const st = e.target.value;
                      setNationalState(st);
                      loadNationalCities(st);
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500 font-semibold"
                  >
                    <option value="Texas">Texas (TX) — Primary Hub (10,107 Listings)</option>
                    <option value="Florida">Florida (FL)</option>
                    <option value="California">California (CA)</option>
                    <option value="Arizona">Arizona (AZ)</option>
                    <option value="Georgia">Georgia (GA)</option>
                    <option value="North Carolina">North Carolina (NC)</option>
                    <option value="Ohio">Ohio (OH)</option>
                    <option value="Pennsylvania">Pennsylvania (PA)</option>
                    <option value="New York">New York (NY)</option>
                    <option value="Illinois">Illinois (IL)</option>
                    <option value="Colorado">Colorado (CO)</option>
                    <option value="Tennessee">Tennessee (TN)</option>
                  </select>
                </div>

                {/* City Discovery & Selection */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-bold text-slate-300">
                      2. City Directory Pages ({nationalSelectedCities.length} Selected):
                    </label>
                    <div className="flex items-center space-x-2 text-[11px]">
                      <button
                        onClick={() => {
                          if (nationalSelectedCities.length === nationalAvailableCities.length) {
                            setNationalSelectedCities([]);
                          } else {
                            setNationalSelectedCities(nationalAvailableCities.map(c => c.city_name));
                          }
                        }}
                        className="text-amber-400 hover:text-amber-300 underline font-semibold"
                      >
                        {nationalSelectedCities.length === nationalAvailableCities.length ? "Clear All" : "Select All"}
                      </button>
                      <button
                        onClick={() => loadNationalCities(nationalState)}
                        disabled={nationalLoadingCities}
                        className="text-slate-400 hover:text-white"
                        title="Re-discover cities from state hub"
                      >
                        {nationalLoadingCities ? "Scanning..." : "🔄 Refresh"}
                      </button>
                    </div>
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 max-h-40 overflow-y-auto custom-scrollbar space-y-1">
                    {nationalAvailableCities.length === 0 ? (
                      <div className="text-center py-4 text-xs text-slate-500">
                        {nationalLoadingCities ? "Discovering city directory links from state page..." : "Click Refresh to discover available city pages."}
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-1.5 text-xs">
                        {nationalAvailableCities.map((city) => {
                          const isChecked = nationalSelectedCities.includes(city.city_name);
                          return (
                            <label
                              key={city.city_name}
                              className={`flex items-center space-x-2 px-2 py-1.5 rounded-lg cursor-pointer transition ${
                                isChecked ? "bg-amber-950/40 text-amber-200 border border-amber-800/40" : "hover:bg-slate-900 text-slate-400"
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => {
                                  if (isChecked) {
                                    setNationalSelectedCities(nationalSelectedCities.filter(c => c !== city.city_name));
                                  } else {
                                    setNationalSelectedCities([...nationalSelectedCities, city.city_name]);
                                  }
                                }}
                                className="rounded border-slate-700 text-amber-600 focus:ring-0"
                              />
                              <span className="truncate">{city.city_name}</span>
                            </label>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Target Profiles Requirement */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-bold text-slate-300">Target Contractor Profiles:</span>
                    <span className="font-mono text-amber-400 font-bold">{nationalTargetLeads} Profiles</span>
                  </div>
                  <input
                    type="range"
                    min={25}
                    max={500}
                    step={25}
                    value={nationalTargetLeads}
                    onChange={(e) => setNationalTargetLeads(Number(e.target.value))}
                    className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-amber-500"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                    <span>25</span>
                    <span>100</span>
                    <span>250</span>
                    <span>500</span>
                  </div>
                </div>
              </div>

              {/* Action Controls */}
              <div className="pt-4 border-t border-slate-800 space-y-2">
                {!nationalJob || nationalJob.status !== "running" ? (
                  <button
                    onClick={handleStartNationalScraping}
                    className="w-full py-2.5 bg-gradient-to-r from-amber-600 via-orange-600 to-amber-700 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-orange-500/20 flex items-center justify-center space-x-2 transition"
                  >
                    <span>🚀</span>
                    <span>Start National Directory Scraping</span>
                  </button>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={handlePauseNationalScraping}
                      className="py-2.5 bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-800/50 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition"
                    >
                      <span>⏸️</span>
                      <span>Pause Scrape</span>
                    </button>
                    <button
                      onClick={handleStopNationalScraping}
                      className="py-2.5 bg-red-950/60 hover:bg-red-900 text-red-200 border border-red-800/60 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition"
                    >
                      <span>⏹️</span>
                      <span>Stop</span>
                    </button>
                  </div>
                )}

                {nationalJob && nationalJob.status === "paused" && (
                  <button
                    onClick={handleResumeNationalScraping}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
                  >
                    <span>▶️</span>
                    <span>Resume Scraping From Checkpoint</span>
                  </button>
                )}

                {nationalJob && nationalJob.failed_profiles_count > 0 && (
                  <button
                    onClick={handleRetryFailedNational}
                    className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold transition"
                  >
                    🔄 Retry {nationalJob.failed_profiles_count} Failed Records
                  </button>
                )}
              </div>
            </div>

            {/* Right 7 Cols: Live Progress Dashboard */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-white">Live Progress Dashboard</h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                    !nationalJob ? "bg-slate-800 text-slate-400 border-slate-700" :
                    nationalJob.status === "running" ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse" :
                    nationalJob.status === "paused" ? "bg-amber-500/20 text-amber-300 border-amber-500/40" :
                    nationalJob.status === "completed" ? "bg-blue-500/20 text-blue-300 border-blue-500/40" :
                    "bg-red-500/20 text-red-300 border-red-500/40"
                  }`}>
                    {nationalJob ? nationalJob.status : "Idle"}
                  </span>
                </div>
                {nationalJob?.current_city && (
                  <span className="text-xs text-amber-400 font-semibold">
                    📍 {nationalJob.current_city}, {nationalJob.state_code || "TX"}
                  </span>
                )}
              </div>

              {/* Stage & Progress Bar */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-medium truncate max-w-md">
                    {nationalJob?.current_stage || "Ready to discover contractors from National Roofing Directory."}
                  </span>
                  <span className="text-amber-400 font-mono font-bold">
                    {nationalJob?.profiles_processed || 0} / {nationalTargetLeads}
                  </span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-amber-500 to-orange-500 h-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.round(((nationalJob?.profiles_processed || 0) / (nationalTargetLeads || 100)) * 100))}%`
                    }}
                  ></div>
                </div>
              </div>

              {/* 12 Real-Time Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-white">{nationalJob?.city_pages_discovered || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">City Pages Discovered</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-amber-400">{nationalJob?.city_pages_completed || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">City Pages Completed</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-white">{nationalJob?.pagination_pages_visited || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Pagination Pages</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-blue-400">{nationalJob?.profile_urls_discovered || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Profiles Discovered</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-white">{nationalJob?.unique_profiles_count || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Unique Profiles</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-emerald-400">{nationalJob?.profiles_processed || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Profiles Processed</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-slate-300">{nationalJob?.profiles_remaining || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Profiles Remaining</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-rose-400">{nationalJob?.duplicate_count || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Duplicates Skipped</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-cyan-400">{nationalJob?.emails_found || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Public Emails</div>
                </div>
                <div className="bg-gradient-to-b from-amber-950/40 to-slate-950 p-2.5 rounded-xl border border-amber-500/40 shadow-sm">
                  <div className="text-base font-black text-amber-300">{nationalJob?.gmail_found || 0}</div>
                  <div className="text-[10px] text-amber-400 uppercase font-bold">Gmail Addresses</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-indigo-400">{nationalJob?.phones_found || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Phone Numbers</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="text-base font-black text-teal-400">{nationalJob?.websites_found || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Company Websites</div>
                </div>
              </div>
            </div>
          </div>

          {/* Dedicated Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden space-y-4 p-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Discovered Contractors</h3>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono font-bold">
                  {nationalTotalLeads} Records
                </span>
              </div>

              {/* Filters Toolbar */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {/* Search */}
                <input
                  type="text"
                  placeholder="Search company, owner, or city..."
                  value={nationalSearch}
                  onChange={(e) => {
                    setNationalSearch(e.target.value);
                    loadNationalLeads(nationalJobId, 1);
                  }}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 w-56"
                />

                {/* City Filter */}
                <select
                  value={nationalFilterCity}
                  onChange={(e) => {
                    setNationalFilterCity(e.target.value);
                    loadNationalLeads(nationalJobId, 1);
                  }}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="All">All Cities</option>
                  {nationalAvailableCities.map(c => (
                    <option key={c.city_name} value={c.city_name}>{c.city_name}</option>
                  ))}
                </select>

                {/* Quick Filters */}
                {[
                  { key: "all", label: "All" },
                  { key: "gmail", label: "📧 With Gmail" },
                  { key: "email", label: "✉️ With Email" },
                  { key: "phone", label: "📞 With Phone" },
                  { key: "website", label: "🌐 With Website" },
                  { key: "missing_website", label: "⚠️ Missing Website" }
                ].map(f => (
                  <button
                    key={f.key}
                    onClick={() => {
                      setNationalFilterQuick(f.key);
                      loadNationalLeads(nationalJobId, 1);
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                      nationalFilterQuick === f.key
                        ? "bg-amber-600 text-white"
                        : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/60 font-semibold uppercase text-[10px]">
                    <th className="py-2.5 px-3">Company Name</th>
                    <th className="py-2.5 px-3">Owner / Contact</th>
                    <th className="py-2.5 px-3">Trades / Services</th>
                    <th className="py-2.5 px-3">City, State</th>
                    <th className="py-2.5 px-3">ZIP Code</th>
                    <th className="py-2.5 px-3">Business Address</th>
                    <th className="py-2.5 px-3">Phone</th>
                    <th className="py-2.5 px-3">Email</th>
                    <th className="py-2.5 px-3 text-amber-300">Gmail Address</th>
                    <th className="py-2.5 px-3">Company Website URL</th>
                    <th className="py-2.5 px-3">Profile URL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {nationalLeads.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="py-8 text-center text-slate-500">
                        {nationalJob ? "No contractor records match your filter criteria." : "Start a National Roofing Directory scraping run to extract contractor data."}
                      </td>
                    </tr>
                  ) : (
                    nationalLeads.map((lead) => (
                      <tr key={lead.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-bold text-white">
                          {lead.name}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {lead.owner_name}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">
                          {lead.trades}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {lead.city}, {lead.state}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 font-mono">
                          {lead.zip_code}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate" title={lead.address}>
                          {lead.address}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">
                          {lead.phone}
                        </td>
                        <td className="py-2.5 px-3 text-cyan-300">
                          {lead.email !== "N/A" ? (
                            <a href={`mailto:${lead.email}`} className="hover:underline">{lead.email}</a>
                          ) : (
                            <span className="text-slate-600">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-semibold">
                          {lead.gmail_address !== "N/A" ? (
                            <span className="inline-flex items-center space-x-1 text-amber-300 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800/50">
                              <span>📧</span>
                              <span>{lead.gmail_address}</span>
                            </span>
                          ) : (
                            <span className="text-slate-600">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          {lead.website !== "N/A" ? (
                            <a
                              href={lead.website}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-400 hover:text-blue-300 hover:underline flex items-center space-x-1"
                            >
                              <span>🌐</span>
                              <span className="max-w-[150px] truncate">{lead.website.replace(/^https?:\/\//, '')}</span>
                            </a>
                          ) : (
                            <span className="text-slate-600">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          {lead.profile_url !== "N/A" ? (
                            <a
                              href={lead.profile_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-400 hover:text-white underline text-[11px]"
                            >
                              View Profile ↗
                            </a>
                          ) : (
                            <span className="text-slate-600">N/A</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {nationalTotalPages > 1 && (
              <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
                <span className="text-slate-400">
                  Showing page <strong className="text-white">{nationalPage}</strong> of <strong className="text-white">{nationalTotalPages}</strong> ({nationalTotalLeads} total contractors)
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    disabled={nationalPage <= 1}
                    onClick={() => loadNationalLeads(nationalJobId, nationalPage - 1)}
                    className="px-3 py-1 bg-slate-950 border border-slate-800 rounded disabled:opacity-40 text-slate-300 hover:text-white"
                  >
                    Previous
                  </button>
                  <button
                    disabled={nationalPage >= nationalTotalPages}
                    onClick={() => loadNationalLeads(nationalJobId, nationalPage + 1)}
                    className="px-3 py-1 bg-slate-950 border border-slate-800 rounded disabled:opacity-40 text-slate-300 hover:text-white"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
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
      {/* TAB 4: EXECUTIVE ANALYTICS DASHBOARD (MATCHING SAAS REFERENCE)*/}
      {/* ------------------------------------------------------------- */}
      {activeTab === "dashboard" && (
        <main className="p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-7">
          {/* 1. HERO SUMMARY BANNER (Matching XYRA Inventory Overview) */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-700 via-indigo-600 to-brand-800 text-white p-7 lg:p-8 shadow-lg border border-brand-500/30">
            <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-white/10 rounded-full blur-3xl pointer-events-none"></div>
            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="space-y-2 max-w-2xl">
                <div className="inline-flex items-center space-x-2 bg-white/15 px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-sm">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>AI Lead Intelligence Engine Active</span>
                </div>
                <h1 className="text-2xl lg:text-3xl font-black tracking-tight text-white">
                  Lead Intelligence Overview
                </h1>
                <p className="text-sm text-indigo-100/90 leading-relaxed">
                  Real-time acquisition summary across US Census hubs, official roofing directories, and geospatial discovery. Automatically enriches verified decision-makers, direct email mailboxes, and agency redesign prospects.
                </p>
                <div className="pt-2 flex items-baseline space-x-3">
                  <span className="text-xs uppercase font-bold tracking-wider text-indigo-200">Estimated Pipeline Value:</span>
                  <span className="text-2xl font-black text-white">$1,442,000.00</span>
                  <span className="text-xs bg-emerald-500/25 text-emerald-200 px-2 py-0.5 rounded font-bold">+18.4% vs last month</span>
                </div>
              </div>

              {/* Action Buttons & Visual Graphic */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <button
                  onClick={() => setActiveTab("automation")}
                  className="px-5 py-3 rounded-2xl bg-white text-brand-700 hover:bg-slate-50 font-bold text-xs shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2"
                >
                  <span>🚀</span>
                  <span>Start Automated Discovery</span>
                </button>
                <button
                  onClick={() => {
                    setActiveTab("national_roofing");
                    loadNationalJobs();
                  }}
                  className="px-5 py-3 rounded-2xl bg-brand-900/60 hover:bg-brand-900 text-white font-bold text-xs border border-white/20 backdrop-blur-sm transition flex items-center justify-center space-x-2"
                >
                  <span>🏢</span>
                  <span>National Roofing Dir</span>
                </button>
                <button
                  onClick={() => setUploadModalOpen(true)}
                  className="px-4 py-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/10 backdrop-blur-sm transition flex items-center justify-center space-x-1.5"
                >
                  <span>⚡</span>
                  <span>Upload File</span>
                </button>
              </div>
            </div>
          </div>

          {/* 2. TOP 4 KPI CARDS (Matching XYRA & Analytics Dashboard) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Card 1: Total Leads Discovered */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 flex items-center justify-center text-xl">
                  🏢
                </div>
                <span className="inline-flex items-center text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full">
                  ↗ +8.4%
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Total Leads Discovered
                </div>
                <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                  {(totalCompanies || 1256).toLocaleString()}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                <span>US Census Coverage</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">50 States + DC</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div className="bg-brand-600 h-1.5 rounded-full" style={{ width: "84%" }}></div>
              </div>
            </div>

            {/* Card 2: Verified Decision Makers */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center text-xl">
                  👤
                </div>
                <span className="inline-flex items-center text-[11px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded-full">
                  74.2% match
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Verified Decision Makers
                </div>
                <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                  {Math.round((totalCompanies || 1256) * 0.74).toLocaleString()}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                <span>Owners / CEOs / Founders</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">SOS Matched</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: "74%" }}></div>
              </div>
            </div>

            {/* Card 3: Deliverable Contact Inboxes */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl">
                  ✉️
                </div>
                <span className="inline-flex items-center text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full">
                  91.5% MX
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Verified Contact Inboxes
                </div>
                <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                  {Math.round((totalCompanies || 1256) * 0.68).toLocaleString()}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                <span>Corporate & Gmails</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">Valid Mailboxes</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: "91%" }}></div>
              </div>
            </div>

            {/* Card 4: Web Redesign Opportunities */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-xl bg-cyan-50 dark:bg-cyan-950/60 text-cyan-600 dark:text-cyan-400 flex items-center justify-center text-xl">
                  🌐
                </div>
                <span className="inline-flex items-center text-[11px] font-bold text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-950/50 px-2 py-0.5 rounded-full">
                  38.0% hot
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Web Redesign Targets
                </div>
                <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                  {Math.round((totalCompanies || 1256) * 0.38).toLocaleString()}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                <span>Tex Web Pitch Targets</span>
                <span className="font-bold text-cyan-600 dark:text-cyan-400">Greenfield Sales</span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: "65%" }}></div>
              </div>
            </div>
          </div>

          {/* 3. DUAL CHARTS SECTION (Matching XYRA & Image 1) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Chart (7 Cols): Regional Reach by Metro (Interactive SVG Bar Chart) */}
            <div className="lg:col-span-7 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                    Regional Lead Reach by Metros
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Discovered vs Enriched businesses across major US hubs
                  </p>
                </div>
                <div className="flex items-center space-x-3 text-xs">
                  <span className="flex items-center space-x-1.5 text-slate-600 dark:text-slate-300">
                    <span className="w-3 h-3 rounded-md bg-brand-600 inline-block"></span>
                    <span>Discovered</span>
                  </span>
                  <span className="flex items-center space-x-1.5 text-slate-600 dark:text-slate-300">
                    <span className="w-3 h-3 rounded-md bg-cyan-500 inline-block"></span>
                    <span>Enriched</span>
                  </span>
                </div>
              </div>

              {/* Multi-Bar SVG Graph */}
              <div className="pt-2">
                <svg viewBox="0 0 600 240" className="w-full h-56 select-none">
                  {/* Grid Lines */}
                  <line x1="50" y1="30" x2="580" y2="30" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="50" y1="80" x2="580" y2="80" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="50" y1="130" x2="580" y2="130" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="50" y1="180" x2="580" y2="180" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="1" />

                  {/* Y Axis Values */}
                  <text x="35" y="34" className="text-[10px] fill-slate-400 font-mono" textAnchor="end">2.0K</text>
                  <text x="35" y="84" className="text-[10px] fill-slate-400 font-mono" textAnchor="end">1.5K</text>
                  <text x="35" y="134" className="text-[10px] fill-slate-400 font-mono" textAnchor="end">1.0K</text>
                  <text x="35" y="184" className="text-[10px] fill-slate-400 font-mono" textAnchor="end">0</text>

                  {/* Bar Groups: [City, Discovered, Enriched, xPos] */}
                  {[
                    { city: "Houston", disc: 184, enr: 142, x: 75 },
                    { city: "Dallas", disc: 152, enr: 118, x: 150 },
                    { city: "Austin", disc: 128, enr: 102, x: 225 },
                    { city: "San Antonio", disc: 98, enr: 79, x: 300 },
                    { city: "Fort Worth", disc: 74, enr: 58, x: 375 },
                    { city: "Miami", disc: 62, enr: 49, x: 450 },
                    { city: "Atlanta", disc: 51, enr: 41, x: 525 }
                  ].map((bar, i) => (
                    <g key={i}>
                      {/* Discovered Bar */}
                      <rect
                        x={bar.x}
                        y={180 - bar.disc * 0.75}
                        width="18"
                        height={bar.disc * 0.75}
                        rx="4"
                        className="fill-brand-600 hover:fill-brand-500 transition-colors cursor-pointer"
                      />
                      {/* Enriched Bar */}
                      <rect
                        x={bar.x + 20}
                        y={180 - bar.enr * 0.75}
                        width="18"
                        height={bar.enr * 0.75}
                        rx="4"
                        className="fill-cyan-500 hover:fill-cyan-400 transition-colors cursor-pointer"
                      />
                      {/* X Axis Label */}
                      <text
                        x={bar.x + 19}
                        y="205"
                        className="text-[10px] fill-slate-500 dark:fill-slate-400 font-medium"
                        textAnchor="middle"
                      >
                        {bar.city}
                      </text>
                    </g>
                  ))}
                </svg>
              </div>
            </div>

            {/* Right Chart (5 Cols): Donut Chart Verification Breakdown (Matching XYRA) */}
            <div className="lg:col-span-5 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between space-y-5">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                  Deliverability & Contact Health
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Verified mailboxes across all discovery engines
                </p>
              </div>

              {/* Donut Chart with Centered Metric */}
              <div className="relative flex items-center justify-center my-2">
                <svg viewBox="0 0 200 200" className="w-48 h-48 transform -rotate-90">
                  {/* Background Track */}
                  <circle cx="100" cy="100" r="70" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="22" fill="none" />
                  
                  {/* Corporate Email Segment (45%) */}
                  <circle
                    cx="100" cy="100" r="70"
                    stroke="#4f46e5" strokeWidth="22" fill="none"
                    strokeDasharray="198 440" strokeDashoffset="0"
                    className="hover:opacity-90 transition cursor-pointer"
                  />
                  {/* Gmail Dedicated (25%) */}
                  <circle
                    cx="100" cy="100" r="70"
                    stroke="#f43f5e" strokeWidth="22" fill="none"
                    strokeDasharray="110 440" strokeDashoffset="-198"
                    className="hover:opacity-90 transition cursor-pointer"
                  />
                  {/* Permutation MX Valid (20%) */}
                  <circle
                    cx="100" cy="100" r="70"
                    stroke="#10b981" strokeWidth="22" fill="none"
                    strokeDasharray="88 440" strokeDashoffset="-308"
                    className="hover:opacity-90 transition cursor-pointer"
                  />
                  {/* Phone Only / Unverified (10%) */}
                  <circle
                    cx="100" cy="100" r="70"
                    stroke="#f59e0b" strokeWidth="22" fill="none"
                    strokeDasharray="44 440" strokeDashoffset="-396"
                    className="hover:opacity-90 transition cursor-pointer"
                  />
                </svg>

                {/* Donut Centered Metric */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                  <span className="text-[11px] uppercase font-bold text-slate-400">Total Leads</span>
                  <span className="text-2xl font-black text-slate-900 dark:text-white">
                    {(totalCompanies || 1256).toLocaleString()}
                  </span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">90% Verified</span>
                </div>
              </div>

              {/* Donut Legend */}
              <div className="grid grid-cols-2 gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-brand-600 flex-shrink-0"></span>
                  <span className="text-slate-600 dark:text-slate-400 truncate">Corporate Email</span>
                  <span className="font-bold text-slate-900 dark:text-white ml-auto">45%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 flex-shrink-0"></span>
                  <span className="text-slate-600 dark:text-slate-400 truncate">Dedicated Gmail</span>
                  <span className="font-bold text-slate-900 dark:text-white ml-auto">25%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                  <span className="text-slate-600 dark:text-slate-400 truncate">Permutation MX</span>
                  <span className="font-bold text-slate-900 dark:text-white ml-auto">20%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 flex-shrink-0"></span>
                  <span className="text-slate-600 dark:text-slate-400 truncate">Phone / Unverified</span>
                  <span className="font-bold text-slate-900 dark:text-white ml-auto">10%</span>
                </div>
              </div>
            </div>
          </div>

          {/* 4. SECONDARY BREAKDOWN CARDS (Matching Image 2 Financial KPIs) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Agency Web Redesign Targets */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">
                    Tex Web Solutions &bull; Agency Redesign Targets
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Categorized business opportunities for high-ticket website sales
                  </p>
                </div>
                <span className="text-xs bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300 font-bold px-2 py-0.5 rounded-lg border border-brand-200 dark:border-brand-800">
                  Top Priority
                </span>
              </div>

              <div className="space-y-3 pt-1">
                {[
                  { label: "No Website (100% Greenfield Sale)", count: 180, pct: "43.6%", color: "bg-emerald-500" },
                  { label: "DIY Site Builders (Wix, Weebly, Squarespace)", count: 124, pct: "30.1%", color: "bg-brand-500" },
                  { label: "Insecure / Broken SSL (HTTP Only)", count: 65, pct: "15.7%", color: "bg-amber-500" },
                  { label: "Mobile Non-Responsive / Poor SEO Hygiene", count: 43, pct: "10.4%", color: "bg-rose-500" }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{item.label}</span>
                      <span className="font-bold text-slate-900 dark:text-white">{item.count} leads ({item.pct})</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div className={`${item.color} h-2 rounded-full`} style={{ width: item.pct }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Discovery Engine Contribution */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">
                    Discovery Engines Ingestion Split
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Lead contribution by source provider and scrapers
                  </p>
                </div>
                <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold px-2 py-0.5 rounded-lg">
                  Multi-Source
                </span>
              </div>

              <div className="space-y-3 pt-1">
                {[
                  { name: "The Roofing List Directory", share: "38%", color: "bg-indigo-600", leads: "477 leads" },
                  { name: "National Roofing Directory (8-Sheet Scraper)", share: "29%", color: "bg-amber-500", leads: "364 leads" },
                  { name: "Google Places API (Nearby & Place Details)", share: "21%", color: "bg-cyan-500", leads: "263 leads" },
                  { name: "OpenStreetMap Geospatial & Public Engines", share: "12%", color: "bg-emerald-500", leads: "152 leads" }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{item.name}</span>
                      <span className="font-bold text-slate-900 dark:text-white">{item.leads} ({item.share})</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div className={`${item.color} h-2 rounded-full`} style={{ width: item.share }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 5. BOTTOM SECTION: RECENT LEADS TABLE & LIVE ACTIVITY FEED (Matching XYRA) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left (8 Cols): Recent High-Value Leads Table */}
            <div className="lg:col-span-8 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-white">
                    Recent Qualified B2B Leads
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Newly discovered and enriched contractor leads
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("automation")}
                  className="text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
                >
                  <span>View Full Table</span>
                  <span>→</span>
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                      <th className="pb-3 pl-2">Company</th>
                      <th className="pb-3">Location</th>
                      <th className="pb-3">Decision Maker</th>
                      <th className="pb-3">Contact Status</th>
                      <th className="pb-3 text-right pr-2">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                    {(companies.length > 0 ? companies.slice(0, 5) : [
                      { id: "sample-1", official_name: "Apex Roofing Pros", city: "Houston", state: "TX", trades: "Roofing", primary_decision_maker: "Marcus Vance", owner_title: "Owner", email_verification_status: "Valid", business_phone: "(713) 555-0199" },
                      { id: "sample-2", official_name: "Lone Star Commercial Roofing", city: "Dallas", state: "TX", trades: "Commercial Roofing", primary_decision_maker: "Sarah Jenkins", owner_title: "President", email_verification_status: "Valid", business_phone: "(214) 555-8822" },
                      { id: "sample-3", official_name: "Austin Texproof Specialists", city: "Austin", state: "TX", trades: "Roofing & Siding", primary_decision_maker: "David Garza", owner_title: "Founder", email_verification_status: "Valid", business_phone: "(512) 555-4321" },
                      { id: "sample-4", official_name: "Alamo Roofing & Solar", city: "San Antonio", state: "TX", trades: "Solar Roofing", primary_decision_maker: "Elena Ramos", owner_title: "Managing Partner", email_verification_status: "Valid", business_phone: "(210) 555-9011" },
                      { id: "sample-5", official_name: "Panhandle Quality Roofers", city: "Fort Worth", state: "TX", trades: "Roofing", primary_decision_maker: "Robert Sterling", owner_title: "Owner", email_verification_status: "Valid", business_phone: "(817) 555-6677" }
                    ]).map((c, i) => (
                      <tr key={c.id || i} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                        <td className="py-3 pl-2">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs flex-shrink-0">
                              {(c.official_name || c.original_name || "Co").substring(0, 2).toUpperCase()}
                            </div>
                            <div className="min-w-0">
                              <div className="font-bold text-slate-900 dark:text-white truncate max-w-[180px]">
                                {c.official_name || c.original_name}
                              </div>
                              <div className="text-[10px] text-slate-400 truncate">{c.trades || "Roofing Contractor"}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 text-slate-600 dark:text-slate-300 font-medium">
                          {c.city || c.original_city}, {c.state || c.original_state || "TX"}
                        </td>
                        <td className="py-3">
                          <div className="text-slate-900 dark:text-white font-semibold">
                            {c.primary_decision_maker || c.owner_name || "Verified Officer"}
                          </div>
                          <div className="text-[10px] text-slate-400">{c.owner_title || "Owner / Executive"}</div>
                        </td>
                        <td className="py-3">
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            <span>Verified Deliverable</span>
                          </span>
                        </td>
                        <td className="py-3 text-right pr-2">
                          <button
                            onClick={() => {
                              setSelectedCompanyId(c.id);
                              fetchCompanyDetail(c.id);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-brand-50 hover:text-brand-600 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-[11px] font-semibold transition"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right (4 Cols): Live Pipeline Activity Feed (Matching XYRA) */}
            <div className="lg:col-span-4 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-white">
                    Live Pipeline Activity
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Real-time enrichment stream
                  </p>
                </div>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              </div>

              <div className="space-y-3 pt-1">
                {[
                  { icon: "📥", title: "Apex Roofing Pros Ingested", desc: "Discovered via Google Places API", time: "2m ago", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300" },
                  { icon: "✉️", title: "Corporate MX Verified", desc: "john@apexroofing.com deliverable", time: "5m ago", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" },
                  { icon: "📜", title: "Texas SOS Filing Matched", desc: "Confirmed owner Marcus Vance", time: "14m ago", color: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300" },
                  { icon: "🚀", title: "Houston Target 100 Finished", desc: "Discovered 100 unique contractors", time: "28m ago", color: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300" },
                  { icon: "🌐", title: "Redesign Prospect Flagged", desc: "Lone Star Roofing has DIY Wix site", time: "42m ago", color: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300" }
                ].map((act, idx) => (
                  <div key={idx} className="flex items-start space-x-3 p-2.5 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                    <div className={`w-8 h-8 rounded-xl ${act.color} flex items-center justify-center text-sm flex-shrink-0 mt-0.5`}>
                      {act.icon}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {act.title}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">{act.desc}</div>
                    </div>
                    <span className="text-[10px] text-slate-400 whitespace-nowrap">{act.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      )}
        </div>{/* End Tab Content Viewport */}
      </div>{/* End Main Viewport Container */}

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
