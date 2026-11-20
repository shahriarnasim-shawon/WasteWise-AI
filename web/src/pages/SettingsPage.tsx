import React, { useState, useEffect } from 'react';
import { translations } from '../i18n';
import { Language, ModelStatus } from '../types';
import { 
  Settings as SettingsIcon, ShieldCheck, Database, 
  RotateCcw, Sliders, CheckCircle2, AlertCircle 
} from 'lucide-react';

interface SettingsPageProps {
  lang: Language;
  modelStatus: ModelStatus | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ lang, modelStatus }) => {
  const t = translations[lang];

  const [calibrationData, setCalibrationData] = useState<any>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/config/calibration')
      .then(res => res.json())
      .then(data => setCalibrationData(data))
      .catch(console.error);
  }, []);

  const handleResetData = async () => {
    if (!confirm("Are you sure you want to reset and re-initialize all database tables?")) return;
    setIsResetting(true);
    setResetMessage(null);
    try {
      const res = await fetch('/api/system/reset', { method: 'POST' });
      const data = await res.json();
      setResetMessage("Database tables successfully cleared and re-initialized.");
    } catch (err: any) {
      setResetMessage(`Reset failed: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const classes = calibrationData?.classes || {};

  return (
    <div className="space-y-4">
      
      {/* Top Banner */}
      <div className="bg-white border border-border p-4 rounded">
        <h2 className="text-base font-semibold text-zinc-900 flex items-center space-x-2">
          <SettingsIcon className="w-4 h-4 text-primary" />
          <span>System Settings & Model Registry</span>
        </h2>
        <p className="text-xs text-zinc-500 mt-1">
          Inference runtime configuration, portion calibration matrix, privacy settings, and database management.
        </p>
      </div>

      {/* Model & Runtime Status */}
      <div className="bg-white border border-border rounded p-4">
        <div className="pb-3 border-b border-border mb-3">
          <h3 className="font-semibold text-sm text-zinc-900">Inference Engine & Model Registry Status</h3>
          <p className="text-xs text-zinc-500">Drop-in loading for Kaggle YOLOv8-nano ONNX weights</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-zinc-50 border border-border rounded">
            <span className="text-[11px] text-zinc-500 block">Active Inference Mode</span>
            <span className="font-mono font-bold text-zinc-900 text-sm mt-1 inline-block">
              {modelStatus?.is_mock ? 'Deterministic Mock Mode' : 'ONNX Runtime CPU'}
            </span>
            <p className="text-[10px] text-zinc-500 mt-1">
              {modelStatus?.mock_reason || 'Inference engine ready'}
            </p>
          </div>

          <div className="p-3 bg-zinc-50 border border-border rounded">
            <span className="text-[11px] text-zinc-500 block">Target Model File Path</span>
            <span className="font-mono text-zinc-700 text-xs mt-1 block truncate">
              {modelStatus?.model_path || 'models/best.onnx'}
            </span>
            <span className={`text-[10px] font-medium mt-1 inline-block ${
              modelStatus?.model_exists ? 'text-emerald-700' : 'text-amber-700'
            }`}>
              {modelStatus?.model_exists ? '✓ Model file present' : '○ Model file missing (Mock fallback active)'}
            </span>
          </div>

          <div className="p-3 bg-zinc-50 border border-border rounded">
            <span className="text-[11px] text-zinc-500 block">Target Latency & Hardware</span>
            <span className="font-mono font-bold text-zinc-900 text-sm mt-1 inline-block">
              &lt; 400 ms (CPU Optimized)
            </span>
            <p className="text-[10px] text-zinc-500 mt-1">
              Supports Render Standard CPU instances without GPU requirement
            </p>
          </div>
        </div>
      </div>

      {/* Portion Calibration Table */}
      <div className="bg-white border border-border rounded p-4">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
          <div>
            <h3 className="font-semibold text-sm text-zinc-900">Portion Calibration Matrix & Economic Parameters</h3>
            <p className="text-xs text-zinc-500">Loaded dynamically from config/portion_calibration.yaml</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">
            Plate Reference: {calibrationData?.plate_reference?.standard_diameter_cm || 26.0} cm
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50 text-zinc-500 border-b border-border font-medium">
              <tr>
                <th className="py-2 px-2.5">Food Class</th>
                <th className="py-2 px-2.5">Name (EN / BN)</th>
                <th className="py-2 px-2.5 font-mono">Density (g/cm²)</th>
                <th className="py-2 px-2.5 font-mono">Std Portion</th>
                <th className="py-2 px-2.5 font-mono">Cost (BDT)</th>
                <th className="py-2 px-2.5 font-mono">Floor Price</th>
                <th className="py-2 px-2.5 font-mono">Shelf Life</th>
                <th className="py-2 px-2.5">Waste Routing</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Object.entries(classes).map(([key, c]: [string, any]) => (
                <tr key={key} className="hover:bg-zinc-50/60">
                  <td className="py-2 px-2.5 font-mono font-semibold text-zinc-900">{key}</td>
                  <td className="py-2 px-2.5 text-zinc-700">
                    {c.name_en} <span className="text-zinc-400">({c.name_bn})</span>
                  </td>
                  <td className="py-2 px-2.5 font-mono">{c.grams_per_cm2}</td>
                  <td className="py-2 px-2.5 font-mono">{c.standard_portion_grams} g</td>
                  <td className="py-2 px-2.5 font-mono">৳{c.unit_cost_bdt}</td>
                  <td className="py-2 px-2.5 font-mono font-medium text-emerald-800">৳{c.floor_price_bdt}</td>
                  <td className="py-2 px-2.5 font-mono">{c.shelf_life_hours}h</td>
                  <td className="py-2 px-2.5 capitalize text-zinc-600">{c.waste_category.replace('_', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Privacy & Compliance Card */}
      <div className="bg-white border border-border rounded p-4 text-xs">
        <div className="flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-emerald-700 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-semibold text-zinc-900">Privacy & Data Governance By Design</h4>
            <p className="text-zinc-600 leading-relaxed text-[11px]">
              WasteWiseAI operates under a zero-facial-storage policy. Cameras focus strictly downwards onto dish return conveyors and kitchen prep counters. Raw image frames are discarded immediately after bounding box and area quantification by default (<code className="bg-zinc-100 px-1 py-0.5 rounded">STORE_IMAGES_DEFAULT=false</code>). Only numerical detections and aggregate leftover metrics are persisted to the database.
            </p>
          </div>
        </div>
      </div>

      {/* Database Reset Action */}
      <div className="bg-white border border-border rounded p-4 flex items-center justify-between text-xs">
        <div>
          <h4 className="font-semibold text-zinc-900">System Database Management</h4>
          <p className="text-zinc-500 mt-0.5">Reset database tables and restore initial seeded operational state.</p>
          {resetMessage && (
            <p className="text-emerald-700 font-medium mt-1">{resetMessage}</p>
          )}
        </div>

        <button
          onClick={handleResetData}
          disabled={isResetting}
          className="px-3 py-1.5 bg-rose-50 border border-rose-300 text-rose-800 hover:bg-rose-100 rounded font-medium flex items-center space-x-1 transition-colors flex-shrink-0"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span>{isResetting ? 'Resetting...' : 'Reset & Re-seed Database'}</span>
        </button>
      </div>
    </div>
  );
};

