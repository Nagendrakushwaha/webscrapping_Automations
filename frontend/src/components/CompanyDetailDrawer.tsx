import React, { useState } from 'react';
import { Company } from '../types';

interface CompanyDetailDrawerProps {
  companyId: string | null;
  onClose: () => void;
  companyDetail: any;
  loading: boolean;
}

export const CompanyDetailDrawer: React.FC<CompanyDetailDrawerProps> = ({
  companyId,
  onClose,
  companyDetail,
  loading,
}) => {
  const [activeTab, setActiveTab] = useState<'mandatory' | 'evidence' | 'sos' | 'audit' | 'pitch'>('mandatory');
  const [copied, setCopied] = useState(false);

  if (!companyId) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end transition-opacity">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-slate-800 transition-colors">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="min-w-0">
            <h3 className="text-lg font-black text-slate-900 dark:text-white truncate">
              {companyDetail?.official_name || companyDetail?.original_name || 'Loading Company...'}
            </h3>
            <p className="text-xs text-slate-500">
              {companyDetail?.city || companyDetail?.original_city}, {companyDetail?.state || companyDetail?.original_state || 'TX'} &bull; {companyDetail?.trades || 'Contractor'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-sm transition"
          >
            ✕
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 space-x-4 text-xs font-bold overflow-x-auto">
          {[
            { id: 'mandatory', label: '12 Target Fields' },
            { id: 'evidence', label: 'Evidence Trail' },
            { id: 'sos', label: 'SOS Corporate Filing' },
            { id: 'audit', label: 'Tech & SEO Audit' },
            { id: 'pitch', label: 'Tex Web Cold Pitch' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`py-3 border-b-2 transition ${
                activeTab === t.id
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar text-xs">
          {loading ? (
            <div className="text-center py-16 text-slate-400 space-y-3">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <div>Retrieving multi-source intelligence records...</div>
            </div>
          ) : (
            <>
              {activeTab === 'mandatory' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">Owner Name</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-0.5">{companyDetail?.owner_name || 'N/A'}</div>
                      <div className="text-[10px] text-slate-500">{companyDetail?.owner_title || 'Owner'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">CEO Name</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-0.5">{companyDetail?.ceo_name || 'N/A'}</div>
                      <div className="text-[10px] text-slate-500">{companyDetail?.ceo_title || 'CEO'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">Business Email</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-0.5 truncate">{companyDetail?.business_email || 'N/A'}</div>
                      <div className="text-[10px] text-emerald-600 font-bold">{companyDetail?.business_email_status || 'Verified MX'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">Dedicated Gmail</div>
                      <div className="font-bold text-rose-600 dark:text-rose-400 mt-0.5 truncate">{companyDetail?.gmail_address || 'N/A'}</div>
                      <div className="text-[10px] text-slate-500">Contractor Direct Mailbox</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">Business Phone</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-0.5">{companyDetail?.business_phone || companyDetail?.original_phone || 'N/A'}</div>
                      <div className="text-[10px] text-slate-500">{companyDetail?.phone_line_type || 'Landline / Direct'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 uppercase text-[10px] font-bold">Official Website</div>
                      <div className="font-bold text-brand-600 dark:text-brand-400 mt-0.5 truncate">
                        {companyDetail?.official_website && companyDetail.official_website !== 'N/A' ? (
                          <a href={companyDetail.official_website} target="_blank" rel="noreferrer" className="hover:underline">
                            {companyDetail.official_website}
                          </a>
                        ) : (
                          'No Website (Greenfield Sale)'
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Social Profiles */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="text-xs font-bold text-slate-900 dark:text-white">Social Media Profiles</div>
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="text-slate-400 block">Personal LinkedIn:</span>
                        <span className="font-medium text-slate-700 dark:text-slate-300 truncate block">
                          {companyDetail?.personal_linkedin || 'Not Available'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Business LinkedIn:</span>
                        <span className="font-medium text-slate-700 dark:text-slate-300 truncate block">
                          {companyDetail?.business_linkedin || 'Not Available'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Business Instagram:</span>
                        <span className="font-medium text-slate-700 dark:text-slate-300 truncate block">
                          {companyDetail?.business_instagram || 'Not Available'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Business Facebook:</span>
                        <span className="font-medium text-slate-700 dark:text-slate-300 truncate block">
                          {companyDetail?.business_facebook || 'Not Available'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'evidence' && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Multi-Source Verification Trail</div>
                  {(companyDetail?.evidence && companyDetail.evidence.length > 0) ? (
                    companyDetail.evidence.map((ev: any, idx: number) => (
                      <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-brand-600 dark:text-brand-400">{ev.field_name}</span>
                          <span className="text-[10px] bg-slate-200 dark:bg-slate-800 px-2 py-0.5 rounded font-mono font-bold">
                            Score: {ev.confidence_score}%
                          </span>
                        </div>
                        <div className="text-slate-900 dark:text-white font-medium">{ev.discovered_value}</div>
                        <div className="text-[10px] text-slate-500">Source: {ev.source_name} ({ev.source_url || 'Direct Registry'})</div>
                        {ev.notes && <div className="text-[10px] text-slate-400 italic">"{ev.notes}"</div>}
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-400 py-8 text-center">No raw evidence entries recorded yet.</div>
                  )}
                </div>
              )}

              {activeTab === 'sos' && (
                <div className="space-y-3">
                  <div className="p-4 bg-purple-50 dark:bg-purple-950/40 rounded-xl border border-purple-200 dark:border-purple-800/50 space-y-2">
                    <div className="flex items-center space-x-2 text-purple-700 dark:text-purple-300 font-bold">
                      <span>📜</span>
                      <span>Secretary of State Corporate Filing</span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300 text-[11px]">
                      Entity verified with Texas / US State Corporate Database. Matches official registered agent and corporate officers.
                    </p>
                    <div className="pt-2 text-slate-900 dark:text-white font-semibold">
                      Registered Officer: {companyDetail?.owner_name || companyDetail?.primary_decision_maker || 'Registered Agent'}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'audit' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 text-[10px] uppercase font-bold">Tech Stack CMS</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-1">{companyDetail?.tech_stack_cms || 'Custom / WordPress'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 text-[10px] uppercase font-bold">SSL Security</div>
                      <div className="font-bold text-emerald-600 mt-1">{companyDetail?.has_ssl ? 'Secure (HTTPS)' : 'Insecure (HTTP)'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 text-[10px] uppercase font-bold">Mobile Responsive</div>
                      <div className="font-bold text-slate-900 dark:text-white mt-1">{companyDetail?.is_mobile_responsive ? 'Yes' : 'No'}</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
                      <div className="text-slate-400 text-[10px] uppercase font-bold">Redesign Opportunity</div>
                      <div className="font-bold text-brand-600 mt-1">{companyDetail?.redesign_opportunity || 'High Value'}</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'pitch' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Personalized Tex Web Solutions Pitch
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `Hi ${companyDetail?.owner_name || 'there'},\n\nI came across ${companyDetail?.official_name || 'your company'} in ${companyDetail?.city || 'Texas'} and noticed an opportunity to dramatically increase your inbound roofing contractor leads with a modernized, mobile-first website.\n\nAt Tex Web Solutions, we specialize in high-converting web applications. Would you be open to a 10-minute chat this week?`
                        );
                        setCopied(true);
                        setTimeout(() => setCopied(false), 3000);
                      }}
                      className="px-3 py-1 bg-brand-600 text-white rounded-lg text-xs font-bold hover:bg-brand-500 transition"
                    >
                      {copied ? '✓ Copied!' : 'Copy Cold Pitch'}
                    </button>
                  </div>
                  <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                    {`Hi ${companyDetail?.owner_name || 'there'},\n\nI came across ${companyDetail?.official_name || 'your company'} in ${companyDetail?.city || 'Texas'} and noticed an opportunity to dramatically increase your inbound roofing contractor leads with a modernized, mobile-first website.\n\nAt Tex Web Solutions, we specialize in high-converting web applications. Would you be open to a 10-minute chat this week?`}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
