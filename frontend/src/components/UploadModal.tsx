import React, { useState } from 'react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [mappings, setMappings] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/jobs/upload-preview', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
        setMappings(data.detected_mappings || {});
      } else {
        alert('Failed to parse file preview.');
      }
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartJob = async () => {
    if (!file) return;
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('column_mappings', JSON.stringify(mappings));

    try {
      const res = await fetch('/api/jobs/upload', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        onUploadSuccess();
        onClose();
      } else {
        alert('Failed to create enrichment job.');
      }
    } catch (err: any) {
      alert(`Job creation error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-2xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto custom-scrollbar shadow-2xl transition-colors">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-extrabold text-slate-900 dark:text-white">Upload Excel / CSV Leads File</h3>
            <p className="text-xs text-slate-500 mt-0.5">Parse headers and map contractor columns for deep enrichment</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-sm transition"
          >
            ✕
          </button>
        </div>

        {!preview ? (
          <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 hover:border-brand-500 rounded-2xl p-10 text-center cursor-pointer transition">
            <input
              type="file"
              accept=".xlsx,.csv"
              onChange={handleFileChange}
              className="hidden"
              id="fileUploadInput"
            />
            <label htmlFor="fileUploadInput" className="cursor-pointer space-y-3 block">
              <div className="text-4xl">📁</div>
              <div className="text-sm font-bold text-slate-900 dark:text-white">
                {loading ? 'Reading and Parsing File...' : 'Click to select XLSX or CSV file'}
              </div>
              <div className="text-xs text-slate-400 max-w-sm mx-auto">
                Supports columns: id, name, trades, city, state, phone, website url, claimed
              </div>
            </label>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 font-semibold flex items-center space-x-2">
              <span>✓</span>
              <span>Loaded: {preview.filename} ({preview.total_rows} businesses detected)</span>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-900 dark:text-white">Confirm Field Mappings:</div>
              <div className="grid grid-cols-2 gap-3 bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
                {[
                  { key: 'id', label: 'Lead ID' },
                  { key: 'name', label: 'Company Name' },
                  { key: 'trades', label: 'Trades / Category' },
                  { key: 'city', label: 'City' },
                  { key: 'state', label: 'State' },
                  { key: 'phone', label: 'Phone' },
                  { key: 'website_url', label: 'Official Website' },
                ].map((f) => (
                  <div key={f.key} className="space-y-1">
                    <label className="text-slate-500 block font-medium">{f.label}</label>
                    <select
                      value={mappings[f.key] || ''}
                      onChange={(e) => setMappings({ ...mappings, [f.key]: e.target.value })}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 dark:text-white"
                    >
                      <option value="">-- Unmapped --</option>
                      {preview.headers.map((h: string) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setPreview(null)}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl"
              >
                Choose Another File
              </button>
              <button
                onClick={handleStartJob}
                disabled={loading}
                className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-md transition"
              >
                {loading ? 'Creating Job...' : 'Start Lead Enrichment Job'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

