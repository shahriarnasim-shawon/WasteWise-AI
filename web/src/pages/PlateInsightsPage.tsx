import React from 'react';
import { translations } from '../i18n';
import { Language } from '../types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid 
} from 'recharts';
import { CheckCircle2, AlertCircle, Sparkles, TrendingUp, HelpCircle } from 'lucide-react';

interface PlateInsightsPageProps {
  lang: Language;
}

export const PlateInsightsPage: React.FC<PlateInsightsPageProps> = ({ lang }) => {
  const t = translations[lang];

  const leftoverDistributionData = [
    { range: '0-20g (Clean)', count: 420, label: 'Clean plates' },
    { range: '21-60g (Trace)', count: 95, label: 'Bones / gravy residue' },
    { range: '61-120g (Light)', count: 68, label: 'Small rice leftover' },
    { range: '121-200g (Med)', count: 42, label: 'Half-eaten portion' },
    { range: '>200g (Heavy)', count: 18, label: 'Untouched order surplus' },
  ];

  const topWastedDishes = [
    { rank: 1, dish: 'Bhuna Khichuri', dish_bn: 'ভুনা খিচুড়ি', avg_leftover_g: 82, waste_rate: '25.2%', reason: 'Heavy standard portions (300g). Students struggle to finish during lunch rush.' },
    { rank: 2, dish: 'Chicken Curry', dish_bn: 'মুরগির মাংস', avg_leftover_g: 48, waste_rate: '15.6%', reason: 'Cooked bones and excess gravy left on plate rims.' },
    { rank: 3, dish: 'Fish Curry', dish_bn: 'মাছের ঝোল', avg_leftover_g: 38, waste_rate: '12.6%', reason: 'Fish bones and mustard/turmeric curry broth residue.' },
    { rank: 4, dish: 'Mixed Vegetable', dish_bn: 'সবজি ভাজি', avg_leftover_g: 32, waste_rate: '10.4%', reason: 'Served in fixed combo with rice even when declined.' },
  ];

  const recentScanGallery = [
    { id: 'SCAN-8092', state: 'empty_plate', state_label: 'Clean Plate (0g)', image_url: '/demo/sample_plates/plate_01_clean_empty.jpg', time: '2 mins ago', items: ['None'] },
    { id: 'SCAN-8091', state: 'partial_leftover', state_label: 'Partial Leftover (158g)', image_url: '/demo/sample_plates/plate_02_rice_chicken_leftover.jpg', time: '5 mins ago', items: ['Rice (110g)', 'Chicken Curry (48g)'] },
    { id: 'SCAN-8090', state: 'partial_leftover', state_label: 'Partial Leftover (235g)', image_url: '/demo/sample_plates/plate_03_khichuri_egg_leftover.jpg', time: '9 mins ago', items: ['Bhuna Khichuri (190g)', 'Egg (45g)'] },
    { id: 'SCAN-8089', state: 'partial_leftover', state_label: 'Partial Leftover (92g)', image_url: '/demo/sample_plates/plate_04_dal_vegetable_leftover.jpg', time: '14 mins ago', items: ['Dal (52g)', 'Vegetable (40g)'] },
  ];

  return (
    <div className="space-y-4">
      
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Clean Plate Rate (Empty Plates)</div>
          <div className="text-2xl font-bold font-mono text-emerald-800 mt-1">78.4%</div>
          <div className="text-[11px] text-emerald-700 mt-1 flex items-center">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            <span>Target: &gt;75% (Canteen efficiency benchmark)</span>
          </div>
        </div>

        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Average Leftover per Scraped Plate</div>
          <div className="text-2xl font-bold font-mono text-zinc-900 mt-1">68.5 g</div>
          <div className="text-[11px] text-zinc-500 mt-1">
            Down from 112g baseline (-38.8%)
          </div>
        </div>

        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Full / Untouched Plate Incidents</div>
          <div className="text-2xl font-bold font-mono text-terracotta mt-1">2.8%</div>
          <div className="text-[11px] text-zinc-500 mt-1">
            18 out of 643 meals served today
          </div>
        </div>
      </div>

      {/* Grid: Leftover Distribution & Most Wasted Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Leftover Distribution Chart */}
        <div className="bg-white border border-border rounded p-4">
          <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
            <div>
              <h3 className="font-semibold text-sm text-zinc-900">Leftover Weight Distribution Histogram</h3>
              <p className="text-xs text-zinc-500">Distribution across 643 monitored meal returns</p>
            </div>
            <span className="text-xs font-mono text-zinc-400">Today</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={leftoverDistributionData} margin={{ top: 10, right: 10, left: -15, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#71717a' }} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#71717a' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e4e4e7', fontSize: '11px' }}
                  formatter={(val: any) => [`${val} plates`, 'Count']} 
                />
                <Bar dataKey="count" fill="#1e3a2b" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Most Wasted Dishes Leaderboard */}
        <div className="bg-white border border-border rounded p-4">
          <div className="pb-3 border-b border-border mb-3">
            <h3 className="font-semibold text-sm text-zinc-900">Top Leftover Dishes & Root Causes</h3>
            <p className="text-xs text-zinc-500">Actionable operational insights for canteen head cook</p>
          </div>

          <div className="space-y-2.5">
            {topWastedDishes.map((item) => (
              <div key={item.rank} className="p-2.5 bg-zinc-50 border border-border rounded text-xs">
                <div className="flex items-center justify-between font-medium">
                  <div className="flex items-center space-x-2">
                    <span className="w-4 h-4 rounded-full bg-zinc-200 text-zinc-700 flex items-center justify-center font-mono text-[10px] font-bold">
                      {item.rank}
                    </span>
                    <span className="text-zinc-900 font-semibold">
                      {lang === 'bn' ? item.dish_bn : item.dish}
                    </span>
                  </div>
                  <div className="text-right font-mono">
                    <span className="text-terracotta font-semibold">{item.waste_rate}</span>
                    <span className="text-zinc-400 ml-1.5 text-[11px]">({item.avg_leftover_g}g / plate)</span>
                  </div>
                </div>
                <p className="text-[11px] text-zinc-600 mt-1 pl-6 leading-relaxed">
                  {item.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gallery of Recent Scan Snapshots */}
      <div className="bg-white border border-border rounded p-4">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
          <div>
            <h3 className="font-semibold text-sm text-zinc-900">Recent Plate Scans Audit Gallery</h3>
            <p className="text-xs text-zinc-500">Visual verification of camera classification and segmentation</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">Live Dish Return Line</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {recentScanGallery.map((scan) => (
            <div key={scan.id} className="border border-border rounded overflow-hidden bg-zinc-50 text-xs">
              <div className="aspect-square bg-zinc-200 relative">
                <img 
                  src={scan.image_url} 
                  alt={scan.id} 
                  className="w-full h-full object-cover" 
                  onError={(e) => {
                    // Fallback to placeholder if asset not yet loaded
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
                <span className={`absolute top-2 left-2 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                  scan.state === 'empty_plate' ? 'bg-emerald-600 text-white' : 'bg-amber-700 text-white'
                }`}>
                  {scan.state === 'empty_plate' ? 'Clean' : 'Leftover'}
                </span>
              </div>
              <div className="p-2.5">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="font-mono text-zinc-600 font-semibold">{scan.id}</span>
                  <span className="text-zinc-400 text-[10px]">{scan.time}</span>
                </div>
                <div className="text-zinc-700 font-medium text-[11px] mt-1">
                  {scan.state_label}
                </div>
                <div className="text-[10px] text-zinc-500 mt-0.5 font-mono truncate">
                  {scan.items.join(', ')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

