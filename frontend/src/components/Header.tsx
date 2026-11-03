import React from 'react';

interface HeaderProps {
  activeTab: string;
  globalSearch: string;
  setGlobalSearch: (s: string) => void;
  onNewSearch: () => void;
  onExport: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  globalSearch,
  setGlobalSearch,
  onNewSearch,
  onExport,
}) => {
  const getTabTitle = (tab: string) => {
    switch (tab) {
      case 'dashboard':
        return 'Executive Analytics Dashboard';
      case 'automation':
        return 'Automated Lead Generation';
      case 'national_roofing':
        return 'National Roofing Directory';
      case 'enrichment':
        return 'Manual Lead Enrichment';
      case 'history':
        return 'Automation History & Logs';
      default:
        return 'AI Lead Intelligence';
    }
  };

  return (
    <header className="sticky top-0 z-20 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-8 py-3.5 flex items-center justify-between transition-colors">
      {/* Breadcrumb / Title */}
      <div className="flex items-center space-x-3">
        <h2 className="text-base font-extrabold text-slate-900 dark:text-white capitalize">
          {getTabTitle(activeTab)}
        </h2>
        <span className="text-slate-300 dark:text-slate-700">/</span>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
          {activeTab === 'dashboard' ? 'System Overview' : 'B2B Acquisition Engine'}
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
            onChange={(e) => setGlobalSearch(e.target.value)}
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
          onClick={onNewSearch}
          className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition shadow-sm flex items-center space-x-1.5"
        >
          <span>+</span>
          <span>New Search</span>
        </button>

        <button
          onClick={onExport}
          className="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold transition border border-slate-200 dark:border-slate-700/80 flex items-center space-x-1.5"
        >
          <span>⬇</span>
          <span>Export CSV</span>
        </button>
      </div>
    </header>
  );
};

