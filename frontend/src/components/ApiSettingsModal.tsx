import React, { useState } from 'react';
import { ApiConfig } from '../types';

interface ApiSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiConfigs: ApiConfig[];
  onSaveKey: (provider: string, key: string) => void;
  onTestKey: (provider: string) => void;
  testingProvider: string | null;
  testResult: Record<string, { success: boolean; message: string }>;
  webhookUrl: string;
  setWebhookUrl: (url: string) => void;
  proxyUrl: string;
  setProxyUrl: (url: string) => void;
}

export const ApiSettingsModal: React.FC<ApiSettingsModalProps> = ({
  isOpen,
  onClose,
  apiConfigs,
  onSaveKey,
  onTestKey,
  testingProvider,
  testResult,
  webhookUrl,
  setWebhookUrl,
  proxyUrl,
  setProxyUrl,
}) => {
  const [keysInput, setKeysInput] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto custom-scrollbar shadow-2xl transition-colors">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-extrabold text-slate-900 dark:text-white">API & Gateway Settings</h3>
            <p className="text-xs text-slate-500 mt-0.5">Configure discovery sources, LLM enrichment, and webhooks</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-sm transition"
          >
            ✕
          </button>
        </div>

        {/* Webhook Settings */}
        <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 dark:text-white text-xs">CRM Outbound Webhook Integration</span>
            <span className="text-[10px] bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300 px-2 py-0.5 rounded font-bold">Auto Push</span>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="https://hooks.zapier.com/hooks/catch/... or Make.com"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400"
            />
            <button
              onClick={() => {
                localStorage.setItem('saved_webhook_url', webhookUrl);
                alert('Webhook URL saved to browser storage!');
              }}
              className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-bold transition shadow-sm"
            >
              Save
            </button>
          </div>
        </div>

        {/* Proxy Rotation */}
        <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 dark:text-white text-xs">Residential Proxy Rotation (Optional)</span>
            <span className="text-[10px] text-slate-400">Anti-Bot Bypass</span>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="http://user:pass@gate.smartproxy.com:7000 or BrightData"
              value={proxyUrl}
              onChange={(e) => setProxyUrl(e.target.value)}
              className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400"
            />
            <button
              onClick={() => {
                localStorage.setItem('saved_proxy_url', proxyUrl);
                alert('Proxy settings saved!');
              }}
              className="px-3.5 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-bold transition"
            >
              Save
            </button>
          </div>
        </div>

        {/* API Providers */}
        <div className="space-y-3 pt-1">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            Third-Party Data & LLM Keys
          </span>

          {apiConfigs.map((cfg) => (
            <div
              key={cfg.provider_name}
              className="bg-slate-50 dark:bg-slate-950 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 dark:text-white text-xs capitalize">
                  {cfg.provider_name.replace('_', ' ')}
                </span>
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    cfg.is_connected ? 'bg-emerald-500' : cfg.has_key ? 'bg-amber-500' : 'bg-slate-400'
                  }`}
                ></span>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="password"
                  placeholder={`Enter ${cfg.provider_name} Key`}
                  defaultValue={cfg.has_key ? '••••••••••••••••' : ''}
                  onChange={(e) => setKeysInput({ ...keysInput, [cfg.provider_name]: e.target.value })}
                  className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400"
                />
                <button
                  onClick={() => {
                    const key = keysInput[cfg.provider_name];
                    if (key && !key.includes('•')) {
                      onSaveKey(cfg.provider_name, key);
                    }
                  }}
                  className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-bold transition shadow-sm"
                >
                  Save
                </button>
                <button
                  disabled={testingProvider === cfg.provider_name}
                  onClick={() => onTestKey(cfg.provider_name)}
                  className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-bold transition"
                >
                  {testingProvider === cfg.provider_name ? 'Testing...' : 'Test'}
                </button>
              </div>
              {testResult[cfg.provider_name] && (
                <p
                  className={`text-[11px] ${
                    testResult[cfg.provider_name].success ? 'text-emerald-600' : 'text-rose-600'
                  }`}
                >
                  {testResult[cfg.provider_name].message}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
