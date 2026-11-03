import React from 'react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  theme: string;
  toggleTheme: () => void;
  onOpenSettings: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
  setCollapsed,
  theme,
  toggleTheme,
  onOpenSettings,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard & Analytics', icon: '📊' },
    { id: 'automation', label: 'Automated Discovery', icon: '🚀', badge: 'Live' },
    { id: 'national_roofing', label: 'National Roofing Dir', icon: '🏢', badge: 'New' },
    { id: 'enrichment', label: 'Manual Enrichment', icon: '⚡' },
    { id: 'history', label: 'Run History & Logs', icon: '📜' },
  ];

  return (
    <aside
      className={`${
        collapsed ? 'w-20' : 'w-64'
      } flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800 flex flex-col justify-between z-30 transition-all duration-200 shadow-sm sticky top-0 h-screen`}
    >
      <div className="flex flex-col h-full overflow-y-auto custom-scrollbar p-4 space-y-6">
        {/* Brand Logo & Title */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800/60">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-accent-500 flex items-center justify-center font-black text-xl text-white shadow-md shadow-brand-500/25 flex-shrink-0">
              T
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <div className="flex items-center space-x-1.5">
                  <h1 className="text-sm font-extrabold tracking-tight text-slate-900 dark:text-white truncate">
                    AI LEAD INTEL
                  </h1>
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
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition text-xs"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        {/* Navigation Section */}
        <div className="space-y-1">
          {!collapsed && (
            <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider px-3 mb-2 block">
              Modules & Analytics
            </span>
          )}

          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center ${
                  collapsed ? 'justify-center px-2' : 'justify-between px-3.5'
                } py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 shadow-sm border border-brand-200/60 dark:border-brand-800/50'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-base">{item.icon}</span>
                  {!collapsed && <span>{item.label}</span>}
                </div>
                {!collapsed && item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded-md font-bold uppercase ${
                      item.badge === 'Live'
                        ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                        : 'bg-amber-500/20 text-amber-700 dark:text-amber-300'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}

          {/* API Settings */}
          <button
            onClick={onOpenSettings}
            className={`w-full flex items-center ${
              collapsed ? 'justify-center px-2' : 'justify-between px-3.5'
            } py-2.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60 transition-all`}
          >
            <div className="flex items-center space-x-3">
              <span className="text-base">⚙️</span>
              {!collapsed && <span>API & Gateway Keys</span>}
            </div>
          </button>
        </div>

        {/* Bottom Sidebar Widgets */}
        <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/60 space-y-3">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`w-full flex items-center ${
              collapsed ? 'justify-center' : 'justify-between px-3'
            } py-2 rounded-xl text-xs font-semibold bg-slate-100/70 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 transition`}
            title="Toggle Light / Dark Mode"
          >
            <div className="flex items-center space-x-2">
              <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
              {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
            </div>
            {!collapsed && (
              <span className="text-[10px] text-slate-400 uppercase font-mono">{theme}</span>
            )}
          </button>

          {/* System Status Pill */}
          {!collapsed && (
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
          {!collapsed && (
            <div className="flex items-center space-x-3 px-1 pt-1">
              <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-300">
                TW
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                  Tex Web Solutions
                </div>
                <div className="text-[10px] text-slate-400 truncate">Administrator</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
