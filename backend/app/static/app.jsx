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

function App() {
  // State
  const [jobs, setJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(15);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [hasOwnerFilter, setHasOwnerFilter] = useState(null);
  const [hasEmailFilter, setHasEmailFilter] = useState(null);
  const [hasLinkedInFilter, setHasLinkedInFilter] = useState(null);

  // Modals & Drawer
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [apiModalOpen, setApiModalOpen] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [companyDetail, setCompanyDetail] = useState(null);
  const [drawerTab, setDrawerTab] = useState("mandatory"); // mandatory, evidence, identity, raw

  // Upload & Mapping Flow
  const [uploadFile, setUploadFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [columnMappings, setColumnMappings] = useState({});
  const [researchSettings, setResearchSettings] = useState({
    industry: "Roofing",
    country: "USA",
    concurrency: 3,
    batch_size: 50,
    attempt_all_12_fields: true,
    enabled_sources: ["website", "tavily", "google_places", "google_search", "bing", "brave", "duckduckgo", "apollo", "hunter"]
  });
  const [isUploading, setIsUploading] = useState(false);

  // API Configs
  const [apiConfigs, setApiConfigs] = useState([]);
  const [testingProvider, setTestingProvider] = useState("");
  const [testResult, setTestResult] = useState({});

  // 1. Initial Load
  useEffect(() => {
    loadJobs();
    loadApiConfigs();
  }, []);

  // 2. Poll Active Job
  useEffect(() => {
    let interval = null;
    if (currentJob && (currentJob.status === "processing" || currentJob.status === "pending")) {
      interval = setInterval(async () => {
        try {
          const updated = await apiFetch(`/api/jobs/${currentJob.id}`);
          setCurrentJob(updated);
          loadCompanies(currentJob.id, currentPage);
          if (updated.status === "completed" || updated.status === "stopped" || updated.status === "failed") {
            clearInterval(interval);
            loadJobs();
          }
        } catch (e) {
          console.error(e);
        }
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [currentJob?.id, currentJob?.status, currentPage]);

  // 3. Load Companies when filters or page change
  useEffect(() => {
    if (currentJob?.id) {
      loadCompanies(currentJob.id, currentPage);
    }
  }, [currentJob?.id, currentPage, searchQuery, statusFilter, hasOwnerFilter, hasEmailFilter, hasLinkedInFilter]);

  // Load Drawer details
  useEffect(() => {
    if (selectedCompanyId) {
      apiFetch(`/api/companies/${selectedCompanyId}`)
        .then(setCompanyDetail)
        .catch(console.error);
    } else {
      setCompanyDetail(null);
    }
  }, [selectedCompanyId]);

  async function loadJobs() {
    try {
      const data = await apiFetch("/api/jobs");
      setJobs(data);
      if (data.length > 0 && !currentJob) {
        setCurrentJob(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function loadApiConfigs() {
    try {
      const data = await apiFetch("/api/settings");
      setApiConfigs(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function loadCompanies(jobId, page = 1) {
    try {
      let url = `/api/companies/job/${jobId}?page=${page}&limit=${pageSize}`;
      if (searchQuery) url += `&q=${encodeURIComponent(searchQuery)}`;
      if (statusFilter !== "All") url += `&status=${encodeURIComponent(statusFilter)}`;
      if (hasOwnerFilter !== null) url += `&has_owner=${hasOwnerFilter}`;
      if (hasEmailFilter !== null) url += `&has_email=${hasEmailFilter}`;
      if (hasLinkedInFilter !== null) url += `&has_linkedin=${hasLinkedInFilter}`;

      const res = await apiFetch(url);
      setCompanies(res.items);
      setTotalCompanies(res.total);
      setTotalPages(res.total_pages);
    } catch (e) {
      console.error(e);
    }
  }

  // --- Handlers ---
  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadFile(file);
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/jobs/upload-preview", {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error("Upload preview failed");
      const data = await res.json();
      setPreviewData(data);
      setColumnMappings(data.detected_mappings);
    } catch (err) {
      alert("Error parsing file: " + err.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleStartResearch() {
    if (!previewData) return;
    setIsUploading(true);
    try {
      const payload = {
        file_id: previewData.file_id,
        mappings: columnMappings,
        settings: researchSettings
      };
      const newJob = await apiFetch("/api/jobs/start-research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      setUploadModalOpen(false);
      setPreviewData(null);
      setCurrentJob(newJob);
      loadJobs();
      setCurrentPage(1);
    } catch (err) {
      alert("Error starting research: " + err.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleJobControl(action) {
    if (!currentJob) return;
    try {
      const updated = await apiFetch(`/api/jobs/${currentJob.id}/control`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
      });
      setCurrentJob(updated);
      loadJobs();
    } catch (err) {
      alert("Action failed: " + err.message);
    }
  }

  async function handleSaveApiKey(providerName, apiKey, extraConfig = {}) {
    try {
      await apiFetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_name: providerName,
          api_key: apiKey,
          extra_config: extraConfig,
          is_enabled: true
        })
      });
      loadApiConfigs();
      alert(`API key for ${providerName} saved securely!`);
    } catch (err) {
      alert("Failed to save: " + err.message);
    }
  }

  async function handleTestApi(providerName, apiKey) {
    setTestingProvider(providerName);
    setTestResult(prev => ({ ...prev, [providerName]: { testing: true } }));
    try {
      const res = await apiFetch("/api/settings/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_name: providerName, api_key: apiKey })
      });
      setTestResult(prev => ({ ...prev, [providerName]: { success: res.success, message: res.message } }));
      loadApiConfigs();
    } catch (err) {
      setTestResult(prev => ({ ...prev, [providerName]: { success: false, message: err.message } }));
    } finally {
      setTestingProvider("");
    }
  }

  // Helper for confidence badge
  function renderConfidenceBadge(score) {
    let color = "bg-rose-900/60 text-rose-300 border-rose-700/60";
    if (score >= 90) color = "bg-emerald-900/60 text-emerald-300 border-emerald-700/60";
    else if (score >= 75) color = "bg-blue-900/60 text-blue-300 border-blue-700/60";
    else if (score >= 50) color = "bg-amber-900/60 text-amber-300 border-amber-700/60";

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${color}`}>
        {score}%
      </span>
    );
  }

  function renderStatusBadge(status) {
    let style = "bg-slate-800 text-slate-300 border-slate-700";
    if (status === "Fully Verified" || status === "Found and Verified") style = "bg-emerald-950 text-emerald-400 border-emerald-800";
    else if (status === "Partially Verified" || status === "Found but Unverified") style = "bg-blue-950 text-blue-400 border-blue-800";
    else if (status === "Requires Manual Review" || status === "Conflicting Information") style = "bg-amber-950 text-amber-400 border-amber-800";
    else if (status === "Not Found") style = "bg-slate-900 text-slate-500 border-slate-800";
    else if (status === "Failed") style = "bg-rose-950 text-rose-400 border-rose-800";

    return (
      <span className={`px-2 py-0.5 text-xs rounded border font-medium ${style}`}>
        {status}
      </span>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* 1. Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-black text-xl shadow-lg shadow-blue-500/20 text-white">
            AI
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">AI LEAD INTELLIGENCE</h1>
              <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">
                v1.0 Production
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Developed for <span className="text-slate-200 font-semibold">Tex Web Solutions Pvt. Ltd.</span> &bull; Web Design &bull; SEO &bull; Digital Solutions
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Active Job Selector */}
          {jobs.length > 0 && (
            <select
              value={currentJob?.id || ""}
              onChange={(e) => {
                const j = jobs.find(x => x.id === e.target.value);
                setCurrentJob(j);
                setCurrentPage(1);
              }}
              className="bg-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:border-blue-500"
            >
              {jobs.map(j => (
                <option key={j.id} value={j.id}>
                  {j.filename.replace(/^upload_[a-f0-9]+/, "File")} ({j.total_companies} leads) - {j.status.toUpperCase()}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => setApiModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            <span>⚙️</span>
            <span>API Settings</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
          </button>

          <button
            onClick={() => {
              setPreviewData(null);
              setUploadFile(null);
              setUploadModalOpen(true);
            }}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/30 transition"
          >
            <span>⬆️ Upload Leads (XLSX / CSV)</span>
          </button>
        </div>
      </header>

      {/* 2. Main Content Area */}
      <main className="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* KPI Metrics Cards */}
        {currentJob && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Total Leads</span>
              <p className="text-xl font-bold text-white mt-1">{currentJob.total_companies}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Processed</span>
              <p className="text-xl font-bold text-blue-400 mt-1">{currentJob.processed_companies}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Enriched</span>
              <p className="text-xl font-bold text-cyan-400 mt-1">{currentJob.enriched_count}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Fully Verified</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">{currentJob.fully_verified_count}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Partially Verified</span>
              <p className="text-xl font-bold text-amber-400 mt-1">{currentJob.partially_verified_count}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Unverified</span>
              <p className="text-xl font-bold text-slate-300 mt-1">{currentJob.unverified_count}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Not Found</span>
              <p className="text-xl font-bold text-slate-500 mt-1">{currentJob.not_found_count}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-sm">
              <span className="text-[11px] font-medium text-slate-400">Manual Review</span>
              <p className="text-xl font-bold text-purple-400 mt-1">{currentJob.manual_review_count}</p>
            </div>
          </div>
        )}

        {/* Live Progress Bar Banner */}
        {currentJob && (
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex-1 w-full space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${
                    currentJob.status === "processing" ? "bg-emerald-500 animate-ping" : 
                    currentJob.status === "paused" ? "bg-amber-500" : "bg-slate-500"
                  }`}></span>
                  <span className="font-semibold text-slate-200 uppercase tracking-wider">
                    Status: {currentJob.status}
                  </span>
                  {currentJob.current_company_name && (
                    <span className="text-slate-400">
                      &bull; Researching: <strong className="text-blue-400">{currentJob.current_company_name}</strong>
                    </span>
                  )}
                  {currentJob.current_stage && (
                    <span className="px-2 py-0.5 text-[10px] rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {currentJob.current_stage}
                    </span>
                  )}
                </div>
                <span className="font-bold text-blue-400">{currentJob.progress_percentage || 0}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-600 to-indigo-500 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${currentJob.progress_percentage || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              {currentJob.status === "processing" ? (
                <button
                  onClick={() => handleJobControl("pause")}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-600/20 text-amber-300 border border-amber-600/40 hover:bg-amber-600/30 transition"
                >
                  ⏸ Pause
                </button>
              ) : currentJob.status === "paused" ? (
                <button
                  onClick={() => handleJobControl("resume")}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600/20 text-emerald-300 border border-emerald-600/40 hover:bg-emerald-600/30 transition"
                >
                  ▶ Resume
                </button>
              ) : null}

              {currentJob.status === "processing" || currentJob.status === "paused" ? (
                <button
                  onClick={() => handleJobControl("stop")}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-600/20 text-rose-300 border border-rose-600/40 hover:bg-rose-600/30 transition"
                >
                  ⏹ Stop
                </button>
              ) : null}

              {currentJob.failed_count > 0 && (
                <button
                  onClick={() => handleJobControl("retry_failed")}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-600/20 text-purple-300 border border-purple-600/40 hover:bg-purple-600/30 transition"
                >
                  🔄 Retry Failed ({currentJob.failed_count})
                </button>
              )}

              {/* Exports */}
              <a
                href={`/api/export/${currentJob.id}/excel`}
                download
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm flex items-center space-x-1.5 transition"
              >
                <span>📊 Export Excel</span>
              </a>
              <a
                href={`/api/export/${currentJob.id}/csv`}
                download
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                <span>Export CSV</span>
              </a>
            </div>
          </div>
        )}

        {/* Filter & Search Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex-1 min-w-[260px] relative">
            <input
              type="text"
              placeholder="Search companies, owner, phone, email, city, state..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <span className="absolute left-3 top-2.5 text-slate-500 text-xs">🔍</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Statuses</option>
              <option value="Fully Verified">Fully Verified</option>
              <option value="Partially Verified">Partially Verified</option>
              <option value="Unverified">Unverified</option>
              <option value="Not Found">Not Found</option>
              <option value="Requires Manual Review">Requires Review</option>
            </select>

            {/* Quick Chips */}
            <button
              onClick={() => setHasOwnerFilter(hasOwnerFilter === true ? null : true)}
              className={`px-3 py-2 rounded-lg border font-medium transition ${
                hasOwnerFilter === true 
                  ? "bg-blue-600 text-white border-blue-500" 
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700"
              }`}
            >
              👤 Has Owner
            </button>
            <button
              onClick={() => setHasEmailFilter(hasEmailFilter === true ? null : true)}
              className={`px-3 py-2 rounded-lg border font-medium transition ${
                hasEmailFilter === true 
                  ? "bg-blue-600 text-white border-blue-500" 
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700"
              }`}
            >
              ✉️ Has Email
            </button>
            <button
              onClick={() => setHasLinkedInFilter(hasLinkedInFilter === true ? null : true)}
              className={`px-3 py-2 rounded-lg border font-medium transition ${
                hasLinkedInFilter === true 
                  ? "bg-blue-600 text-white border-blue-500" 
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700"
              }`}
            >
              🔗 Has LinkedIn
            </button>
          </div>
        </div>

        {/* Results Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 divide-y divide-slate-800">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-3">Company & Identity</th>
                  <th className="px-4 py-3">Decision Makers</th>
                  <th className="px-4 py-3">Contacts</th>
                  <th className="px-4 py-3">Personal Contacts</th>
                  <th className="px-4 py-3">LinkedIn & Socials</th>
                  <th className="px-4 py-3 text-center">Confidence</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {companies.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-4 py-12 text-center text-slate-500">
                      {currentJob ? "No companies matched your filter criteria." : "Please upload a leads file to begin research."}
                    </td>
                  </tr>
                ) : (
                  companies.map(c => (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition">
                      {/* 1. Company & Identity */}
                      <td className="px-4 py-3 max-w-[220px]">
                        <p className="font-semibold text-white truncate text-sm">
                          {c.official_name || c.original_name}
                        </p>
                        <p className="text-[11px] text-slate-400 truncate">
                          📍 {c.city ? `${c.city}, ${c.state}` : c.original_city ? `${c.original_city}, ${c.original_state}` : "Location N/A"}
                        </p>
                        {c.official_website ? (
                          <a 
                            href={c.official_website} 
                            target="_blank" 
                            rel="noreferrer"
                            className="text-[11px] text-blue-400 hover:underline truncate block"
                          >
                            🌐 {c.official_website.replace(/^https?:\/\//, '')}
                          </a>
                        ) : (
                          <span className="text-[10px] text-slate-500">No website</span>
                        )}
                      </td>

                      {/* 2. Mandatory Decision Makers (Owner, CEO, Founder, Co-Founder) */}
                      <td className="px-4 py-3 max-w-[200px] space-y-1">
                        {c.owner_name ? (
                          <div>
                            <span className="font-medium text-slate-100">{c.owner_name}</span>
                            <span className="ml-1 text-[10px] px-1.5 py-0.2 bg-blue-900/50 text-blue-300 rounded">Owner</span>
                          </div>
                        ) : null}
                        {c.ceo_name && c.ceo_name !== c.owner_name ? (
                          <div>
                            <span className="font-medium text-slate-200">{c.ceo_name}</span>
                            <span className="ml-1 text-[10px] px-1.5 py-0.2 bg-indigo-900/50 text-indigo-300 rounded">CEO</span>
                          </div>
                        ) : null}
                        {c.founder_name && c.founder_name !== c.owner_name && c.founder_name !== c.ceo_name ? (
                          <div>
                            <span className="font-medium text-slate-300">{c.founder_name}</span>
                            <span className="ml-1 text-[10px] px-1.5 py-0.2 bg-purple-900/50 text-purple-300 rounded">Founder</span>
                          </div>
                        ) : null}
                        {!c.owner_name && !c.ceo_name && !c.founder_name && (
                          <span className="text-slate-500 italic text-[11px]">Not Found</span>
                        )}
                      </td>

                      {/* 3. Business Contacts */}
                      <td className="px-4 py-3 max-w-[190px] space-y-0.5">
                        {c.business_email ? (
                          <div className="flex items-center space-x-1 truncate">
                            <span className="text-slate-400">✉️</span>
                            <span className="text-slate-200 truncate">{c.business_email}</span>
                          </div>
                        ) : (
                          <span className="text-slate-500 block text-[11px]">Email: Not Found</span>
                        )}
                        {c.business_phone ? (
                          <div className="flex items-center space-x-1 truncate">
                            <span className="text-slate-400">📞</span>
                            <span className="text-slate-200">{c.business_phone}</span>
                          </div>
                        ) : (
                          <span className="text-slate-500 block text-[11px]">Phone: Not Found</span>
                        )}
                        {c.email_verification_status && c.email_verification_status !== "Unknown" && (
                          <span className={`text-[9px] px-1 py-0.2 rounded font-semibold ${
                            c.email_verification_status === "Valid" ? "bg-emerald-900/60 text-emerald-300" : "bg-rose-900/60 text-rose-300"
                          }`}>
                            MX: {c.email_verification_status}
                          </span>
                        )}
                      </td>

                      {/* 4. Personal Professional Contacts */}
                      <td className="px-4 py-3 max-w-[170px] space-y-0.5">
                        {c.personal_email ? (
                          <p className="text-indigo-300 truncate">✉️ {c.personal_email}</p>
                        ) : (
                          <p className="text-slate-500 text-[11px]">Personal Email: N/A</p>
                        )}
                        {c.personal_phone ? (
                          <p className="text-indigo-300 truncate">📱 {c.personal_phone}</p>
                        ) : (
                          <p className="text-slate-500 text-[11px]">Personal Phone: N/A</p>
                        )}
                      </td>

                      {/* 5. Social Links */}
                      <td className="px-4 py-3 space-x-1">
                        {c.personal_linkedin && (
                          <a
                            href={c.personal_linkedin}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-blue-900/60 text-blue-300 rounded border border-blue-700/60 hover:bg-blue-800 transition"
                            title="Personal LinkedIn"
                          >
                            in (Person)
                          </a>
                        )}
                        {c.business_linkedin && (
                          <a
                            href={c.business_linkedin}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-sky-900/60 text-sky-300 rounded border border-sky-700/60 hover:bg-sky-800 transition"
                            title="Company LinkedIn"
                          >
                            in (Co)
                          </a>
                        )}
                        {c.business_instagram && (
                          <a
                            href={c.business_instagram}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-pink-900/60 text-pink-300 rounded border border-pink-700/60 hover:bg-pink-800 transition"
                            title="Instagram"
                          >
                            IG
                          </a>
                        )}
                        {c.business_facebook && (
                          <a
                            href={c.business_facebook}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-900/60 text-indigo-300 rounded border border-indigo-700/60 hover:bg-indigo-800 transition"
                            title="Facebook"
                          >
                            FB
                          </a>
                        )}
                        {!c.personal_linkedin && !c.business_linkedin && !c.business_instagram && !c.business_facebook && (
                          <span className="text-slate-500 text-[11px]">None</span>
                        )}
                      </td>

                      {/* 6. Confidence Score */}
                      <td className="px-4 py-3 text-center">
                        {renderConfidenceBadge(c.overall_confidence_score)}
                      </td>

                      {/* 7. Verification Status */}
                      <td className="px-4 py-3 text-center">
                        {renderStatusBadge(c.overall_verification_status)}
                      </td>

                      {/* 8. Action: Open Drawer */}
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setSelectedCompanyId(c.id)}
                          className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white border border-slate-700 hover:border-blue-500 transition"
                        >
                          Evidence & Details &rarr;
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {companies.length} of {totalCompanies} companies
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 disabled:opacity-40 border border-slate-700"
              >
                &larr; Prev
              </button>
              <span className="text-slate-300 font-semibold">Page {currentPage} of {totalPages || 1}</span>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 disabled:opacity-40 border border-slate-700"
              >
                Next &rarr;
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* 3. Slide-Over Evidence Drawer */}
      {selectedCompanyId && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setSelectedCompanyId(null)}
          ></div>
          <div className="relative w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col z-10 custom-scrollbar overflow-y-auto">
            {companyDetail ? (
              <div className="p-6 space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {companyDetail.official_name || companyDetail.original_name}
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Lead ID: <strong className="text-slate-300">{companyDetail.original_id}</strong> &bull; {companyDetail.city}, {companyDetail.state}
                    </p>
                    {companyDetail.official_website && (
                      <a href={companyDetail.official_website} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline mt-0.5 block">
                        🌐 {companyDetail.official_website} ({companyDetail.website_status})
                      </a>
                    )}
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <button 
                      onClick={() => setSelectedCompanyId(null)}
                      className="text-slate-400 hover:text-white text-lg font-bold p-1"
                    >
                      ✕
                    </button>
                    {renderConfidenceBadge(companyDetail.overall_confidence_score)}
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-800 space-x-4 text-xs font-semibold">
                  <button
                    onClick={() => setDrawerTab("mandatory")}
                    className={`pb-2 border-b-2 transition ${drawerTab === "mandatory" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400"}`}
                  >
                    12 Mandatory Fields
                  </button>
                  <button
                    onClick={() => setDrawerTab("evidence")}
                    className={`pb-2 border-b-2 transition ${drawerTab === "evidence" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400"}`}
                  >
                    Evidence Ledger ({companyDetail.evidence?.length || 0})
                  </button>
                  <button
                    onClick={() => setDrawerTab("identity")}
                    className={`pb-2 border-b-2 transition ${drawerTab === "identity" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400"}`}
                  >
                    Company & Website Identity
                  </button>
                  <button
                    onClick={() => setDrawerTab("raw")}
                    className={`pb-2 border-b-2 transition ${drawerTab === "raw" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400"}`}
                  >
                    Original File Data
                  </button>
                </div>

                {/* Tab 1: 12 Mandatory Fields Breakdown */}
                {drawerTab === "mandatory" && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Owner */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">1. Owner</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.owner_name || "Not Found"}</p>
                        <p className="text-[10px] text-slate-500">{companyDetail.owner_title || "Designation N/A"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.owner_status)}</div>
                      </div>

                      {/* CEO */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">2. CEO</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.ceo_name || "Not Found"}</p>
                        <p className="text-[10px] text-slate-500">{companyDetail.ceo_title || "Designation N/A"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.ceo_status)}</div>
                      </div>

                      {/* Founder */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">3. Founder</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.founder_name || "Not Found"}</p>
                        <p className="text-[10px] text-slate-500">{companyDetail.founder_title || "Designation N/A"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.founder_status)}</div>
                      </div>

                      {/* Co-Founder */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">4. Co-Founder</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.cofounder_name || "Not Found"}</p>
                        <p className="text-[10px] text-slate-500">{companyDetail.cofounder_title || "Designation N/A"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.cofounder_status)}</div>
                      </div>

                      {/* Business Email */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">5. Business Email</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.business_email || "Not Found"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.business_email_status)}</div>
                      </div>

                      {/* Business Phone */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">6. Business Phone</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.business_phone || "Not Found"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.business_phone_status)}</div>
                      </div>

                      {/* Personal Professional Email */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">7. Personal Professional Email</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.personal_email || "Not Found"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.personal_email_status)}</div>
                      </div>

                      {/* Public Professional Phone */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">8. Public Professional Phone</span>
                        <p className="font-semibold text-white mt-1">{companyDetail.personal_phone || "Not Found"}</p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.personal_phone_status)}</div>
                      </div>

                      {/* Personal LinkedIn */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">9. Personal LinkedIn</span>
                        <p className="font-semibold text-blue-400 truncate mt-1">
                          {companyDetail.personal_linkedin ? (
                            <a href={companyDetail.personal_linkedin} target="_blank" rel="noreferrer" className="hover:underline">
                              {companyDetail.personal_linkedin}
                            </a>
                          ) : "Not Found"}
                        </p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.personal_linkedin_status)}</div>
                      </div>

                      {/* Business LinkedIn */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">10. Business LinkedIn</span>
                        <p className="font-semibold text-blue-400 truncate mt-1">
                          {companyDetail.business_linkedin ? (
                            <a href={companyDetail.business_linkedin} target="_blank" rel="noreferrer" className="hover:underline">
                              {companyDetail.business_linkedin}
                            </a>
                          ) : "Not Found"}
                        </p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.business_linkedin_status)}</div>
                      </div>

                      {/* Business Instagram */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">11. Business Instagram</span>
                        <p className="font-semibold text-pink-400 truncate mt-1">
                          {companyDetail.business_instagram ? (
                            <a href={companyDetail.business_instagram} target="_blank" rel="noreferrer" className="hover:underline">
                              {companyDetail.business_instagram}
                            </a>
                          ) : "Not Found"}
                        </p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.business_instagram_status)}</div>
                      </div>

                      {/* Business Facebook */}
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-medium">12. Business Facebook</span>
                        <p className="font-semibold text-indigo-400 truncate mt-1">
                          {companyDetail.business_facebook ? (
                            <a href={companyDetail.business_facebook} target="_blank" rel="noreferrer" className="hover:underline">
                              {companyDetail.business_facebook}
                            </a>
                          ) : "Not Found"}
                        </p>
                        <div className="mt-2">{renderStatusBadge(companyDetail.business_facebook_status)}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 2: Evidence Ledger */}
                {drawerTab === "evidence" && (
                  <div className="space-y-3">
                    {companyDetail.evidence?.length === 0 ? (
                      <p className="text-slate-500 text-xs italic text-center py-6">No evidence recorded yet.</p>
                    ) : (
                      companyDetail.evidence.map(ev => (
                        <div key={ev.id} className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white text-sm">{ev.field_name}</span>
                            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-semibold border border-slate-700">
                              {ev.source_name}
                            </span>
                          </div>
                          <p className="text-blue-300 font-mono text-xs bg-slate-900 px-2 py-1 rounded border border-slate-800">
                            {ev.discovered_value}
                          </p>
                          {ev.source_url && (
                            <a 
                              href={ev.source_url} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="text-blue-400 hover:underline block truncate text-[11px]"
                            >
                              🔗 {ev.source_url}
                            </a>
                          )}
                          <p className="text-slate-400 text-[11px]">{ev.notes}</p>
                          <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                            <span>Checked: {new Date(ev.last_checked).toLocaleDateString()}</span>
                            <span>Confidence: {ev.confidence_score}%</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Tab 3: Company & Website Identity */}
                {drawerTab === "identity" && (
                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3 text-xs">
                    <div>
                      <span className="text-slate-400">Full Business Address:</span>
                      <p className="font-semibold text-white mt-0.5">{companyDetail.address || "Address N/A"}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Year Established:</span>
                      <p className="font-semibold text-white mt-0.5">{companyDetail.year_established || "N/A"}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Website Title:</span>
                      <p className="text-slate-200 mt-0.5">{companyDetail.website_title || "N/A"}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Website Meta Description:</span>
                      <p className="text-slate-300 text-[11px] mt-0.5">{companyDetail.website_description || "N/A"}</p>
                    </div>
                    <div className="pt-2 border-t border-slate-800 space-y-1">
                      <span className="text-slate-400 font-semibold">Subpages Discovered:</span>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                        {companyDetail.about_page_url && <li>About Us: <a href={companyDetail.about_page_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{companyDetail.about_page_url}</a></li>}
                        {companyDetail.contact_page_url && <li>Contact Us: <a href={companyDetail.contact_page_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{companyDetail.contact_page_url}</a></li>}
                        {companyDetail.team_page_url && <li>Team / Leadership: <a href={companyDetail.team_page_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{companyDetail.team_page_url}</a></li>}
                        {companyDetail.services_page_url && <li>Services: <a href={companyDetail.services_page_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{companyDetail.services_page_url}</a></li>}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Tab 4: Raw Original Data Preserved */}
                {drawerTab === "raw" && (
                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2 text-xs">
                    <p className="text-slate-400 italic mb-2">Original values preserved intact from uploaded file:</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">id:</strong> {companyDetail.original_id}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">name:</strong> {companyDetail.original_name}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">trades:</strong> {companyDetail.original_trades}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">city:</strong> {companyDetail.original_city}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">state:</strong> {companyDetail.original_state}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">phone:</strong> {companyDetail.original_phone}</div>
                      <div className="bg-slate-900 p-2 rounded col-span-2"><strong className="text-slate-400">website:</strong> {companyDetail.original_website}</div>
                      <div className="bg-slate-900 p-2 rounded"><strong className="text-slate-400">claimed:</strong> {companyDetail.original_claimed}</div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">Loading details...</div>
            )}
          </div>
        </div>
      )}

      {/* 4. Upload & Column Mapping Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setUploadModalOpen(false)}></div>
          <div className="relative bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-5 z-10 custom-scrollbar max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white">Upload Leads & Confirm Column Mapping</h3>
                <p className="text-xs text-slate-400">Upload your company XLSX or CSV file. We will preview and map your columns.</p>
              </div>
              <button onClick={() => setUploadModalOpen(false)} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
            </div>

            {/* Drop Zone */}
            {!previewData ? (
              <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-8 text-center transition bg-slate-950/50">
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileUpload}
                  id="leadFileInput"
                  className="hidden"
                />
                <label htmlFor="leadFileInput" className="cursor-pointer block space-y-2">
                  <div className="text-4xl">📁</div>
                  <p className="text-sm font-semibold text-slate-200">
                    {isUploading ? "Reading and analyzing file..." : "Click to select or drag and drop Excel or CSV file"}
                  </p>
                  <p className="text-xs text-slate-500">Supports .xlsx, .xls, and .csv with original columns</p>
                </label>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-400">File: </span>
                    <strong className="text-white">{previewData.filename}</strong>
                    <span className="text-slate-400 ml-3">Total Rows: </span>
                    <strong className="text-blue-400">{previewData.total_rows}</strong>
                    {previewData.duplicate_count > 0 && (
                      <span className="ml-3 px-2 py-0.5 bg-amber-900/50 text-amber-300 rounded text-[11px]">
                        ⚠️ {previewData.duplicate_count} potential duplicates detected
                      </span>
                    )}
                  </div>
                  <button 
                    onClick={() => { setPreviewData(null); setUploadFile(null); }}
                    className="text-xs text-rose-400 hover:underline"
                  >
                    Change File
                  </button>
                </div>

                {/* Column Mapping Section */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Column Mapping (Confirm or Override)
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    {[
                      { key: "id", label: "1. ID" },
                      { key: "name", label: "2. Name" },
                      { key: "trades", label: "3. Trades / Industry" },
                      { key: "city", label: "4. City" },
                      { key: "state", label: "5. State" },
                      { key: "phone", label: "6. Phone" },
                      { key: "webssite url", label: "7. Website URL" },
                      { key: "claimed", label: "8. Claimed Status" },
                    ].map(f => (
                      <div key={f.key} className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-1">
                        <label className="text-[11px] font-medium text-slate-400 block">{f.label}</label>
                        <select
                          value={columnMappings[f.key] || ""}
                          onChange={(e) => setColumnMappings({ ...columnMappings, [f.key]: e.target.value })}
                          className="w-full bg-slate-900 border border-slate-700 text-white rounded px-2 py-1 text-xs focus:outline-none focus:border-blue-500"
                        >
                          <option value="">-- Ignore --</option>
                          {previewData.headers.map(h => (
                            <option key={h} value={h}>{h}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Research Settings */}
                <div className="space-y-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                  <h4 className="font-bold uppercase tracking-wider text-slate-300">Research Configuration</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-slate-400 block mb-1">Target Industry / Trade</label>
                      <input
                        type="text"
                        value={researchSettings.industry}
                        onChange={(e) => setResearchSettings({ ...researchSettings, industry: e.target.value })}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Country</label>
                      <input
                        type="text"
                        value={researchSettings.country}
                        onChange={(e) => setResearchSettings({ ...researchSettings, country: e.target.value })}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Worker Concurrency</label>
                      <select
                        value={researchSettings.concurrency}
                        onChange={(e) => setResearchSettings({ ...researchSettings, concurrency: parseInt(e.target.value) })}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs"
                      >
                        <option value="1">1 company at a time (Slow)</option>
                        <option value="3">3 concurrent (Recommended)</option>
                        <option value="5">5 concurrent (High speed)</option>
                        <option value="10">10 concurrent</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Preview Table */}
                <div className="space-y-1">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">File Preview (First 5 Rows)</h4>
                  <div className="overflow-x-auto border border-slate-800 rounded-lg max-h-48 custom-scrollbar">
                    <table className="w-full text-left text-[11px] text-slate-300">
                      <thead className="bg-slate-950 text-slate-400 sticky top-0">
                        <tr>
                          {previewData.headers.map(h => (
                            <th key={h} className="px-3 py-1.5 border-b border-slate-800">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {previewData.preview_rows.slice(0, 5).map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/30">
                            {previewData.headers.map(h => (
                              <td key={h} className="px-3 py-1.5 truncate max-w-[140px]">{row[h] || "-"}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800 flex justify-end space-x-3">
                  <button
                    onClick={() => setUploadModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    disabled={isUploading}
                    onClick={handleStartResearch}
                    className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-600/30"
                  >
                    {isUploading ? "Starting Research..." : "Confirm & Start Automatic Research"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. API Settings Modal */}
      {apiModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setApiModalOpen(false)}></div>
          <div className="relative bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 z-10 custom-scrollbar max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white">API & Integration Settings</h3>
                <p className="text-xs text-slate-400">Configure your API credentials. Keys are saved securely in your local environment.</p>
              </div>
              <button onClick={() => setApiModalOpen(false)} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
            </div>

            <div className="space-y-3">
              {apiConfigs.map(cfg => (
                <div key={cfg.provider_name} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white text-xs">{cfg.provider_name}</span>
                      <span className={`w-2 h-2 rounded-full ${cfg.is_connected ? "bg-emerald-500" : cfg.has_key ? "bg-amber-500" : "bg-slate-600"}`}></span>
                      <span className="text-[10px] text-slate-400">
                        {cfg.is_connected ? "Connected" : cfg.has_key ? "Key Saved (Untested)" : "Not Configured"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="password"
                      placeholder={`Enter ${cfg.provider_name} API Key`}
                      defaultValue={cfg.has_key ? "••••••••••••••••" : ""}
                      id={`key_${cfg.provider_name}`}
                      className="flex-1 bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={() => {
                        const val = document.getElementById(`key_${cfg.provider_name}`).value;
                        if (val && !val.includes("•")) {
                          handleSaveApiKey(cfg.provider_name, val);
                        } else {
                          alert("Please enter a new API key to save.");
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
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded text-xs font-medium"
                    >
                      {testingProvider === cfg.provider_name ? "Testing..." : "Test Connection"}
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

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setApiModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

