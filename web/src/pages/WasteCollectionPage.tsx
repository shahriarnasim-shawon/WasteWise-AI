import React, { useState, useEffect } from 'react';
import { translations } from '../i18n';
import { Language, WasteBinItem, ManifestItem } from '../types';
import { 
  Trash2, Download, HeartHandshake, CheckCircle2, 
  Truck, ArrowRight, ShieldCheck 
} from 'lucide-react';

interface WasteCollectionPageProps {
  lang: Language;
}

export const WasteCollectionPage: React.FC<WasteCollectionPageProps> = ({ lang }) => {
  const t = translations[lang];

  const [bins, setBins] = useState<WasteBinItem[]>([]);
  const [manifests, setManifests] = useState<ManifestItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchCollectionData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/agents/collection');
      const data = await res.json();
      if (data.bins && data.bins.length > 0) setBins(data.bins);
      if (data.recent_manifests && data.recent_manifests.length > 0) setManifests(data.recent_manifests);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCollectionData();
  }, []);

  // Seeded fallback bins if DB empty
  const activeBins: WasteBinItem[] = bins.length > 0 ? bins : [
    { id: 1, category: 'edible_surplus', name_en: 'Edible Surplus (Donation)', name_bn: 'উদ্বৃত্ত খাবার (দান)', capacity_kg: 25.0, current_weight_kg: 18.5, fill_percentage: 74.0, destination: 'Local Community NGO / Food Bank', status: 'normal' },
    { id: 2, category: 'animal_feed', name_en: 'Animal Feed', name_bn: 'পশুর খাদ্য', capacity_kg: 40.0, current_weight_kg: 28.0, fill_percentage: 70.0, destination: 'Suburban Poultry & Dairy Farm', status: 'normal' },
    { id: 3, category: 'compost', name_en: 'Organic Compost', name_bn: 'জৈব সার', capacity_kg: 35.0, current_weight_kg: 30.0, fill_percentage: 85.7, destination: 'Campus Organic Compost Unit', status: 'pickup_scheduled' },
    { id: 4, category: 'general', name_en: 'General Waste', name_bn: 'সাধারণ বর্জ্য', capacity_kg: 50.0, current_weight_kg: 14.2, fill_percentage: 28.4, destination: 'City Corporation Waste Management', status: 'normal' },
  ];

  const activeManifests: ManifestItem[] = manifests.length > 0 ? manifests : [
    { id: 1, manifest_code: 'WW-EDIB-20261115-001', timestamp: '2026-11-15T13:45:00', category: 'edible_surplus', total_kg: 18.5, destination: 'Mirpur Community Food Bank', status: 'scheduled', notes: 'Untouched hot counter trays sealed in food-grade insulated containers.' },
    { id: 2, manifest_code: 'WW-COMP-20261115-002', timestamp: '2026-11-15T12:15:00', category: 'compost', total_kg: 30.0, destination: 'Campus Compost Unit', status: 'completed', notes: 'Vegetable trimmings and lentil sediment dispatched.' },
    { id: 3, manifest_code: 'WW-ANIM-20261114-004', timestamp: '2026-11-14T19:30:00', category: 'animal_feed', total_kg: 34.2, destination: 'Savar Poultry Cooperative', status: 'completed', notes: 'Rice and grain scraping feed collected.' },
  ];

  return (
    <div className="space-y-4">
      
      {/* Top Donation Banner */}
      <div className="bg-emerald-50 border border-emerald-300 p-3.5 rounded flex items-center justify-between text-xs text-emerald-950">
        <div className="flex items-center space-x-3">
          <HeartHandshake className="w-5 h-5 text-emerald-700 flex-shrink-0" />
          <div>
            <span className="font-semibold text-emerald-900">Edible Surplus Recovery & Donation Active:</span>
            <p className="text-emerald-800 mt-0.5">
              18.5 kg of untouched hot-counter food (37 meals) tagged for immediate pickup by Local Community NGO. 
              Zero consumable food discarded.
            </p>
          </div>
        </div>
        <a
          href="/api/agents/collection/manifests/export_csv"
          download="wastewise_collection_manifests.csv"
          className="px-3 py-1.5 bg-white border border-emerald-300 text-emerald-900 hover:bg-emerald-100 rounded font-medium flex items-center space-x-1.5 transition-colors shadow-sm flex-shrink-0 ml-4"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Manifests CSV</span>
        </a>
      </div>

      {/* 4 Waste Bin Fill Levels */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {activeBins.map((b) => (
          <div key={b.id} className="bg-white border border-border p-3.5 rounded flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-zinc-900">
                  {lang === 'bn' ? b.name_bn : b.name_en}
                </span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-mono uppercase font-semibold ${
                  b.status === 'pickup_scheduled' ? 'bg-amber-100 text-amber-800' : 'bg-zinc-100 text-zinc-600'
                }`}>
                  {b.status === 'pickup_scheduled' ? 'Pickup Scheduled' : 'Normal'}
                </span>
              </div>

              <div className="text-2xl font-bold font-mono text-zinc-900 mt-2">
                {b.fill_percentage}%
              </div>
              <div className="text-[11px] text-zinc-500 font-mono mt-0.5">
                {b.current_weight_kg.toFixed(1)} kg / {b.capacity_kg} kg capacity
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-zinc-100 h-2 rounded overflow-hidden mt-3 border border-zinc-200">
                <div 
                  className={`h-full transition-all duration-500 ${
                    b.fill_percentage >= 80 ? 'bg-amber-600' : b.fill_percentage >= 60 ? 'bg-primary' : 'bg-emerald-600'
                  }`}
                  style={{ width: `${Math.min(100, b.fill_percentage)}%` }}
                />
              </div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-border text-[11px] text-zinc-500 flex items-center justify-between">
              <span className="truncate" title={b.destination}>{b.destination}</span>
              <Truck className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0 ml-1" />
            </div>
          </div>
        ))}
      </div>

      {/* Manifests & Dispatch Schedule */}
      <div className="bg-white border border-border rounded p-4">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
          <div>
            <h3 className="font-semibold text-sm text-zinc-900">Waste Collection & Routing Manifests</h3>
            <p className="text-xs text-zinc-500">Official chain-of-custody tracking for audits and municipal compliance</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">Total {activeManifests.length} Dispatches</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50 text-zinc-500 border-b border-border font-medium">
              <tr>
                <th className="py-2.5 px-3">Manifest Code</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 font-mono">Weight (kg)</th>
                <th className="py-2.5 px-3">Destination Partner</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {activeManifests.map((m) => (
                <tr key={m.id} className="hover:bg-zinc-50/60">
                  <td className="py-2.5 px-3 font-mono font-medium text-primary">
                    {m.manifest_code}
                  </td>
                  <td className="py-2.5 px-3 text-zinc-500 font-mono">
                    {m.timestamp.slice(0, 16).replace('T', ' ')}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="capitalize font-medium text-zinc-800">
                      {m.category.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono font-bold text-zinc-900">
                    {m.total_kg.toFixed(1)} kg
                  </td>
                  <td className="py-2.5 px-3 text-zinc-700">
                    {m.destination}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                      m.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {m.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-zinc-500 text-[11px] max-w-xs truncate">
                    {m.notes || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

