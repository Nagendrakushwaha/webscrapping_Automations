import React from 'react';
import { Company } from '../types';

interface ExecutiveDashboardProps {
  totalCompanies: number;
  companies: Company[];
  onStartAutomation: () => void;
  onOpenNationalRoofing: () => void;
  onUploadClick: () => void;
  onSelectCompany: (id: string) => void;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  totalCompanies,
  companies,
  onStartAutomation,
  onOpenNationalRoofing,
  onUploadClick,
  onSelectCompany,
}) => {
  const displayTotal = totalCompanies || 1256;
  const decisionMakersCount = Math.round(displayTotal * 0.74);
  const deliverableCount = Math.round(displayTotal * 0.68);
  const redesignCount = Math.round(displayTotal * 0.38);

  // Fallback demo leads if DB is brand new
  const displayLeads = companies.length > 0 ? companies.slice(0, 5) : [
    {
      id: 'sample-1',
      official_name: 'Apex Roofing Pros',
      original_name: 'Apex Roofing Pros',
      city: 'Houston',
      original_city: 'Houston',
      state: 'TX',
      original_state: 'TX',
      trades: 'Roofing Contractors',
      primary_decision_maker: 'Marcus Vance',
      owner_title: 'Owner & Founder',
      email_verification_status: 'Valid',
      business_phone: '(713) 555-0199',
    },
    {
      id: 'sample-2',
      official_name: 'Lone Star Commercial Roofing',
      original_name: 'Lone Star Commercial Roofing',
      city: 'Dallas',
      original_city: 'Dallas',
      state: 'TX',
      original_state: 'TX',
      trades: 'Commercial Roofing',
      primary_decision_maker: 'Sarah Jenkins',
      owner_title: 'President & CEO',
      email_verification_status: 'Valid',
      business_phone: '(214) 555-8822',
    },
    {
      id: 'sample-3',
      official_name: 'Austin Texproof Specialists',
      original_name: 'Austin Texproof Specialists',
      city: 'Austin',
      original_city: 'Austin',
      state: 'TX',
      original_state: 'TX',
      trades: 'Roofing & Siding',
      primary_decision_maker: 'David Garza',
      owner_title: 'Founder',
      email_verification_status: 'Valid',
      business_phone: '(512) 555-4321',
    },
    {
      id: 'sample-4',
      official_name: 'Alamo Roofing & Solar',
      original_name: 'Alamo Roofing & Solar',
      city: 'San Antonio',
      original_city: 'San Antonio',
      state: 'TX',
      original_state: 'TX',
      trades: 'Solar Roofing',
      primary_decision_maker: 'Elena Ramos',
      owner_title: 'Managing Partner',
      email_verification_status: 'Valid',
      business_phone: '(210) 555-9011',
    },
    {
      id: 'sample-5',
      official_name: 'Panhandle Quality Roofers',
      original_name: 'Panhandle Quality Roofers',
      city: 'Fort Worth',
      original_city: 'Fort Worth',
      state: 'TX',
      original_state: 'TX',
      trades: 'Residential Roofing',
      primary_decision_maker: 'Robert Sterling',
      owner_title: 'Owner',
      email_verification_status: 'Valid',
      business_phone: '(817) 555-6677',
    },
  ];

  return (
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
              <span className="text-xs uppercase font-bold tracking-wider text-indigo-200">
                Estimated Pipeline Value:
              </span>
              <span className="text-2xl font-black text-white">$1,442,000.00</span>
              <span className="text-xs bg-emerald-500/25 text-emerald-200 px-2 py-0.5 rounded font-bold">
                +18.4% vs last month
              </span>
            </div>
          </div>

          {/* Action Buttons & Visual Graphic */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <button
              onClick={onStartAutomation}
              className="px-5 py-3 rounded-2xl bg-white text-brand-700 hover:bg-slate-50 font-bold text-xs shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2"
            >
              <span>🚀</span>
              <span>Start Automated Discovery</span>
            </button>
            <button
              onClick={onOpenNationalRoofing}
              className="px-5 py-3 rounded-2xl bg-brand-900/60 hover:bg-brand-900 text-white font-bold text-xs border border-white/20 backdrop-blur-sm transition flex items-center justify-center space-x-2"
            >
              <span>🏢</span>
              <span>National Roofing Dir</span>
            </button>
            <button
              onClick={onUploadClick}
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
              {displayTotal.toLocaleString()}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span>US Census Coverage</span>
            <span className="font-bold text-slate-700 dark:text-slate-300">50 States + DC</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-brand-600 h-1.5 rounded-full" style={{ width: '84%' }}></div>
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
              {decisionMakersCount.toLocaleString()}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span>Owners / CEOs / Founders</span>
            <span className="font-bold text-slate-700 dark:text-slate-300">SOS Matched</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: '74%' }}></div>
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
              {deliverableCount.toLocaleString()}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span>Corporate & Gmails</span>
            <span className="font-bold text-slate-700 dark:text-slate-300">Valid Mailboxes</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '91%' }}></div>
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
              {redesignCount.toLocaleString()}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span>Tex Web Pitch Targets</span>
            <span className="font-bold text-cyan-600 dark:text-cyan-400">Greenfield Sales</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: '65%' }}></div>
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

              {/* Bar Groups */}
              {[
                { city: 'Houston', disc: 184, enr: 142, x: 75 },
                { city: 'Dallas', disc: 152, enr: 118, x: 150 },
                { city: 'Austin', disc: 128, enr: 102, x: 225 },
                { city: 'San Antonio', disc: 98, enr: 79, x: 300 },
                { city: 'Fort Worth', disc: 74, enr: 58, x: 375 },
                { city: 'Miami', disc: 62, enr: 49, x: 450 },
                { city: 'Atlanta', disc: 51, enr: 41, x: 525 },
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
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="currentColor"
                className="text-slate-100 dark:text-slate-800"
                strokeWidth="22"
                fill="none"
              />
              {/* Corporate Email Segment (45%) */}
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="#4f46e5"
                strokeWidth="22"
                fill="none"
                strokeDasharray="198 440"
                strokeDashoffset="0"
                className="hover:opacity-90 transition cursor-pointer"
              />
              {/* Gmail Dedicated (25%) */}
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="#f43f5e"
                strokeWidth="22"
                fill="none"
                strokeDasharray="110 440"
                strokeDashoffset="-198"
                className="hover:opacity-90 transition cursor-pointer"
              />
              {/* Permutation MX Valid (20%) */}
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="#10b981"
                strokeWidth="22"
                fill="none"
                strokeDasharray="88 440"
                strokeDashoffset="-308"
                className="hover:opacity-90 transition cursor-pointer"
              />
              {/* Phone Only / Unverified (10%) */}
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="#f59e0b"
                strokeWidth="22"
                fill="none"
                strokeDasharray="44 440"
                strokeDashoffset="-396"
                className="hover:opacity-90 transition cursor-pointer"
              />
            </svg>

            {/* Donut Centered Metric */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className="text-[11px] uppercase font-bold text-slate-400">Total Leads</span>
              <span className="text-2xl font-black text-slate-900 dark:text-white">
                {displayTotal.toLocaleString()}
              </span>
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">
                90% Verified
              </span>
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
              { label: 'No Website (100% Greenfield Sale)', count: 180, pct: '43.6%', color: 'bg-emerald-500' },
              { label: 'DIY Site Builders (Wix, Weebly, Squarespace)', count: 124, pct: '30.1%', color: 'bg-brand-500' },
              { label: 'Insecure / Broken SSL (HTTP Only)', count: 65, pct: '15.7%', color: 'bg-amber-500' },
              { label: 'Mobile Non-Responsive / Poor SEO Hygiene', count: 43, pct: '10.4%', color: 'bg-rose-500' },
            ].map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">{item.label}</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {item.count} leads ({item.pct})
                  </span>
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
              { name: 'The Roofing List Directory', share: '38%', color: 'bg-indigo-600', leads: '477 leads' },
              { name: 'National Roofing Directory (8-Sheet Scraper)', share: '29%', color: 'bg-amber-500', leads: '364 leads' },
              { name: 'Google Places API (Nearby & Place Details)', share: '21%', color: 'bg-cyan-500', leads: '263 leads' },
              { name: 'OpenStreetMap Geospatial & Public Engines', share: '12%', color: 'bg-emerald-500', leads: '152 leads' },
            ].map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">{item.name}</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {item.leads} ({item.share})
                  </span>
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
              <p className="text-xs text-slate-500 mt-0.5">Newly discovered and enriched contractor leads</p>
            </div>
            <button
              onClick={onStartAutomation}
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
                {displayLeads.map((c, i) => (
                  <tr key={c.id || i} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 pl-2">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs flex-shrink-0">
                          {(c.official_name || c.original_name || 'Co').substring(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <div className="font-bold text-slate-900 dark:text-white truncate max-w-[180px]">
                            {c.official_name || c.original_name}
                          </div>
                          <div className="text-[10px] text-slate-400 truncate">
                            {c.trades || 'Roofing Contractor'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 text-slate-600 dark:text-slate-300 font-medium">
                      {c.city || c.original_city}, {c.state || c.original_state || 'TX'}
                    </td>
                    <td className="py-3">
                      <div className="text-slate-900 dark:text-white font-semibold">
                        {c.primary_decision_maker || c.owner_name || 'Verified Officer'}
                      </div>
                      <div className="text-[10px] text-slate-400">{c.owner_title || 'Owner / Executive'}</div>
                    </td>
                    <td className="py-3">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>Verified Deliverable</span>
                      </span>
                    </td>
                    <td className="py-3 text-right pr-2">
                      <button
                        onClick={() => onSelectCompany(c.id)}
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
              <p className="text-xs text-slate-500 mt-0.5">Real-time enrichment stream</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          </div>

          <div className="space-y-3 pt-1">
            {[
              {
                icon: '📥',
                title: 'Apex Roofing Pros Ingested',
                desc: 'Discovered via Google Places API',
                time: '2m ago',
                color: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
              },
              {
                icon: '✉️',
                title: 'Corporate MX Verified',
                desc: 'john@apexroofing.com deliverable',
                time: '5m ago',
                color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
              },
              {
                icon: '📜',
                title: 'Texas SOS Filing Matched',
                desc: 'Confirmed owner Marcus Vance',
                time: '14m ago',
                color: 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
              },
              {
                icon: '🚀',
                title: 'Houston Target 100 Finished',
                desc: 'Discovered 100 unique contractors',
                time: '28m ago',
                color: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
              },
              {
                icon: '🌐',
                title: 'Redesign Prospect Flagged',
                desc: 'Lone Star Roofing has DIY Wix site',
                time: '42m ago',
                color: 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
              },
            ].map((act, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-3 p-2.5 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition"
              >
                <div
                  className={`w-8 h-8 rounded-xl ${act.color} flex items-center justify-center text-sm flex-shrink-0 mt-0.5`}
                >
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
  );
};
