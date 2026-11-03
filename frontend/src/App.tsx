import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ExecutiveDashboard } from './components/ExecutiveDashboard';
import { CompanyDetailDrawer } from './components/CompanyDetailDrawer';
import { ApiSettingsModal } from './components/ApiSettingsModal';
import { UploadModal } from './components/UploadModal';
import { Company, Job, ApiConfig } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'automation' | 'national_roofing' | 'enrichment' | 'history'>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');
  const [globalSearch, setGlobalSearch] = useState('');

  // Data State
  const [companies, setCompanies] = useState<Company[]>([]);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);

  // Modals & Drawer
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [companyDetail, setCompanyDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);

  // Settings State
  const [apiConfigs, setApiConfigs] = useState<ApiConfig[]>([]);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, { success: boolean; message: string }>>({});
  const [webhookUrl, setWebhookUrl] = useState(() => localStorage.getItem('saved_webhook_url') || '');
  const [proxyUrl, setProxyUrl] = useState(() => localStorage.getItem('saved_proxy_url') || '');

  // Theme Sync
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  // Initial Data Fetch
  useEffect(() => {
    loadJobs();
    loadApiConfigs();
  }, []);

  const loadJobs = async () => {
    try {
      const res = await fetch('/api/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
        if (data.length > 0) {
          setCurrentJob(data[0]);
          loadCompanies(data[0].id);
        }
      }
    } catch (e) {
      console.error('Failed to load jobs:', e);
    }
  };

  const loadCompanies = async (jobId: string) => {
    try {
      const res = await fetch(`/api/companies?job_id=${jobId}&page=1&page_size=20`);
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.items || []);
        setTotalCompanies(data.total || 0);
      }
    } catch (e) {
      console.error('Failed to load companies:', e);
    }
  };

  const loadApiConfigs = async () => {
    try {
      const res = await fetch('/api/settings/api-configs');
      if (res.ok) {
        const data = await res.json();
        setApiConfigs(data);
      }
    } catch (e) {
      console.error('Failed to load API configs:', e);
    }
  };

  const fetchCompanyDetail = async (id: string) => {
    setSelectedCompanyId(id);
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/companies/${id}`);
      if (res.ok) {
        const data = await res.json();
        setCompanyDetail(data);
      }
    } catch (e) {
      console.error('Failed to fetch company detail:', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSaveApiKey = async (provider: string, key: string) => {
    try {
      const res = await fetch(`/api/settings/api-configs/${provider}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: key, is_enabled: true }),
      });
      if (res.ok) {
        loadApiConfigs();
        alert(`${provider} key saved successfully!`);
      }
    } catch (e: any) {
      alert(`Save error: ${e.message}`);
    }
  };

  const handleTestApiKey = async (provider: string) => {
    setTestingProvider(provider);
    try {
      const res = await fetch(`/api/settings/api-configs/${provider}/test`, { method: 'POST' });
      const data = await res.json();
      setTestResult((prev) => ({
        ...prev,
        [provider]: { success: data.is_connected, message: data.message || 'Connected successfully' },
      }));
    } catch (e: any) {
      setTestResult((prev) => ({
        ...prev,
        [provider]: { success: false, message: e.message },
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  const handleExportCSV = () => {
    if (currentJob) {
      window.open(`/api/export/job/${currentJob.id}/excel`, '_blank');
    } else {
      window.open(`/api/export/job/latest/excel`, '_blank');
    }
  };

  return (
    <div className={`min-h-screen flex ${theme === 'dark' ? 'dark bg-slate-950 text-slate-100' : 'bg-[#f8fafc] text-slate-800'} font-sans antialiased transition-colors duration-150`}>
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(t: any) => setActiveTab(t)}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        theme={theme}
        toggleTheme={toggleTheme}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* 2. Main Viewport Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto max-h-screen custom-scrollbar">
        {/* Top Header Bar */}
        <Header
          activeTab={activeTab}
          globalSearch={globalSearch}
          setGlobalSearch={setGlobalSearch}
          onNewSearch={() => setActiveTab('automation')}
          onExport={handleExportCSV}
        />

        {/* Dynamic Views */}
        <div className="flex-1">
          {activeTab === 'dashboard' && (
            <ExecutiveDashboard
              totalCompanies={totalCompanies}
              companies={companies}
              onStartAutomation={() => setActiveTab('automation')}
              onOpenNationalRoofing={() => setActiveTab('national_roofing')}
              onUploadClick={() => setUploadOpen(true)}
              onSelectCompany={fetchCompanyDetail}
            />
          )}

          {activeTab === 'automation' && (
            <div className="p-8 max-w-7xl mx-auto space-y-6">
              <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl p-7 shadow-sm">
                <h3 className="text-xl font-black text-slate-900 dark:text-white">🚀 Automated Lead Generation</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-2xl">
                  Geographic discovery across all 50 US States, official US Census cities, and radius filtering. Discovered leads are enriched with decision-maker emails, phone numbers, and Tex Web Solutions redesign scores.
                </p>
                <div className="pt-4">
                  <a
                    href="/"
                    className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md transition"
                  >
                    <span>Launch Geographic Search Wizard</span>
                    <span>→</span>
                  </a>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'national_roofing' && (
            <div className="p-8 max-w-7xl mx-auto space-y-6">
              <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl p-7 shadow-sm">
                <h3 className="text-xl font-black text-slate-900 dark:text-white">🏢 National Roofing Directory</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-2xl">
                  Multi-state discovery with automated city discovery, rel="next" pagination traversal, isolated Gmail extraction, and 8-sheet Excel workbook export.
                </p>
                <div className="pt-4">
                  <a
                    href="/"
                    className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md transition"
                  >
                    <span>Open National Roofing Scraper</span>
                    <span>→</span>
                  </a>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'enrichment' && (
            <div className="p-8 max-w-7xl mx-auto space-y-6">
              <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl p-7 shadow-sm space-y-4">
                <h3 className="text-xl font-black text-slate-900 dark:text-white">⚡ Manual Lead Enrichment & Upload</h3>
                <p className="text-xs text-slate-500 max-w-2xl">
                  Upload existing spreadsheets (XLSX, CSV). The system automatically maps your columns, audits company websites, verifies Secretary of State corporate filings, and extracts decision-maker contact details.
                </p>
                <div>
                  <button
                    onClick={() => setUploadOpen(true)}
                    className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md transition"
                  >
                    📁 Upload Excel Lead Spreadsheet
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="p-8 max-w-7xl mx-auto space-y-6">
              <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl p-7 shadow-sm">
                <h3 className="text-xl font-black text-slate-900 dark:text-white">📜 Automation History & Scrape Logs</h3>
                <p className="text-xs text-slate-500 mt-1">Audit log of all past scraper jobs, completion rates, and exported files.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals & Drawer */}
      <CompanyDetailDrawer
        companyId={selectedCompanyId}
        onClose={() => setSelectedCompanyId(null)}
        companyDetail={companyDetail}
        loading={detailLoading}
      />

      <ApiSettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        apiConfigs={apiConfigs}
        onSaveKey={handleSaveApiKey}
        onTestKey={handleTestApiKey}
        testingProvider={testingProvider}
        testResult={testResult}
        webhookUrl={webhookUrl}
        setWebhookUrl={setWebhookUrl}
        proxyUrl={proxyUrl}
        setProxyUrl={setProxyUrl}
      />

      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploadSuccess={() => loadJobs()}
      />
    </div>
  );
}
export default App;
