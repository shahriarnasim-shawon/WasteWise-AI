import React, { useState, useEffect } from 'react';
import { translations } from '../i18n';
import { Language } from '../types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend 
} from 'recharts';
import { AlertTriangle, Clock, Layers, TrendingDown, ArrowUpRight } from 'lucide-react';

interface AnalyticsPageProps {
  lang: Language;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ lang }) => {
  const t = translations[lang];

  // Realistic seeded analytics data
  const wasteByDishData = [
    { name: lang === 'bn' ? 'সাদা ভাত' : 'Plain Rice', waste_kg: 42.4, cost_bdt: 3390, pct_served: 8.8 },
    { name: lang === 'bn' ? 'ভুনা খিচুড়ি' : 'Bhuna Khichuri', waste_kg: 68.2, cost_bdt: 9090, pct_served: 25.2 },
    { name: lang === 'bn' ? 'মুরগির মাংস' : 'Chicken Curry', waste_kg: 34.5, cost_bdt: 12075, pct_served: 15.6 },
    { name: lang === 'bn' ? 'মাছের ঝোল' : 'Fish Curry', waste_kg: 22.8, cost_bdt: 7600, pct_served: 12.6 },
    { name: lang === 'bn' ? 'মসুর ডাল' : 'Lentil Dal', waste_kg: 19.5, cost_bdt: 1950, pct_served: 6.1 },
    { name: lang === 'bn' ? 'সবজি ভাজি' : 'Vegetable', waste_kg: 24.0, cost_bdt: 2880, pct_served: 10.4 },
    { name: lang === 'bn' ? 'ডিমের ডালনা' : 'Egg Curry', waste_kg: 14.2, cost_bdt: 2400, pct_served: 7.2 },
    { name: lang === 'bn' ? 'ভর্তা' : 'Bhorta', waste_kg: 8.6, cost_bdt: 1290, pct_served: 5.7 },
  ];

  const mealPeriodData = [
    { period: 'Breakfast (নাস্তা)', waste_kg: 38.5, served_kg: 340, waste_rate: '11.3%' },
    { period: 'Lunch (দুপুরের খাবার)', waste_kg: 152.4, served_kg: 1280, waste_rate: '11.9%' },
    { period: 'Snacks/Dinner (বিকাল/রাত)', waste_kg: 43.3, served_kg: 390, waste_rate: '11.1%' },
  ];

  const inventoryBatches = [
    { batch_id: 'BATCH-KC-204', dish: 'Bhuna Khichuri', dish_bn: 'ভুনা খিচুড়ি', prepared: '11:30 AM', expiry: '03:30 PM', hours_left: '0.8h', stock: 32, discount: '35% Flash Sale', status: 'discounted' },
    { batch_id: 'BATCH-RC-108', dish: 'Plain Rice', dish_bn: 'সাদা ভাত', prepared: '12:00 PM', expiry: '04:00 PM', hours_left: '1.4h', stock: 65, discount: '20% Clearance', status: 'discounted' },
    { batch_id: 'BATCH-CC-302', dish: 'Chicken Curry', dish_bn: 'মুরগির মাংস', prepared: '12:30 PM', expiry: '04:30 PM', hours_left: '2.1h', stock: 45, discount: 'Standard (0%)', status: 'fresh' },
    { batch_id: 'BATCH-FC-401', dish: 'Fish Curry', dish_bn: 'মাছের ঝোল', prepared: '12:45 PM', expiry: '04:45 PM', hours_left: '2.3h', stock: 28, discount: 'Standard (0%)', status: 'fresh' },
    { batch_id: 'BATCH-VG-505', dish: 'Mixed Vegetable', dish_bn: 'সবজি ভাজি', prepared: '01:00 PM', expiry: '06:00 PM', hours_left: '3.6h', stock: 50, discount: 'Standard (0%)', status: 'fresh' },
  ];

  return (
    <div className="space-y-4">
      
      {/* Highlight Alert: Highest Wasted Item */}
      <div className="bg-amber-50 border border-amber-300 p-3 rounded flex items-start space-x-3 text-xs text-amber-900">
        <AlertTriangle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-950">High Leftover Alert — Bhuna Khichuri (Batch #204):</span>
          <p className="text-amber-800 mt-0.5">
            Bhuna Khichuri is averaging 25.2% plate leftover rate today (68.2 kg wasted, ৳9,090 loss). 
            DynamicDiscountAgent has published a 35% discount for the remaining 32 portions. 
            Recommendation: Reduce standard lunchtime kitchen prep by 15% on dry weather days.
          </p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Weekly Food Wasted</div>
          <div className="text-2xl font-bold font-mono text-zinc-900 mt-1">234.2 kg</div>
          <div className="text-[11px] text-emerald-700 mt-1 flex items-center font-medium">
            <TrendingDown className="w-3.5 h-3.5 mr-1" />
            <span>Down 34.6% vs pre-system baseline</span>
          </div>
        </div>

        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Weekly Financial Waste Cost</div>
          <div className="text-2xl font-bold font-mono text-terracotta mt-1">{t.currency} 40,675</div>
          <div className="text-[11px] text-zinc-500 mt-1 font-mono">
            ৳5,810 / day canteen scrap loss
          </div>
        </div>

        <div className="bg-white border border-border p-3.5 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">Surplus Recovered via Dynamic Discounts</div>
          <div className="text-2xl font-bold font-mono text-emerald-800 mt-1">{t.currency} 28,450</div>
          <div className="text-[11px] text-zinc-500 mt-1">
            412 near-expiry portions sold to students
          </div>
        </div>
      </div>

      {/* Waste By Dish Chart */}
      <div className="bg-white border border-border rounded p-4">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
          <div>
            <h3 className="font-semibold text-sm text-zinc-900">Food Waste Volume by Dish (kg)</h3>
            <p className="text-xs text-zinc-500">Aggregated plate scrapings and unserved batch discards</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">Weekly Breakdown</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={wasteByDishData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#71717a' }} angle={-20} textAnchor="end" />
              <YAxis tick={{ fontSize: 11, fill: '#71717a' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e4e4e7', fontSize: '11px' }}
                formatter={(val: any) => [`${val} kg`, 'Waste']} 
              />
              <Bar dataKey="waste_kg" fill="#1e3a2b" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid: Meal Periods & Active Inventory Batches */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Meal Periods Summary */}
        <div className="bg-white border border-border rounded p-4">
          <div className="pb-3 border-b border-border mb-3">
            <h3 className="font-semibold text-sm text-zinc-900">Waste by Meal Period</h3>
            <p className="text-xs text-zinc-500">Breakfast vs Lunch vs Snacks</p>
          </div>

          <div className="space-y-3">
            {mealPeriodData.map((m, idx) => (
              <div key={idx} className="p-2.5 bg-zinc-50 border border-border rounded text-xs">
                <div className="flex justify-between font-medium text-zinc-900">
                  <span>{m.period}</span>
                  <span className="font-mono">{m.waste_kg} kg</span>
                </div>
                <div className="flex justify-between text-zinc-500 text-[11px] mt-1 font-mono">
                  <span>Served: {m.served_kg} kg</span>
                  <span className="text-amber-800 font-semibold">{m.waste_rate} waste</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Current Inventory Batches & Expiry Timers */}
        <div className="lg:col-span-2 bg-white border border-border rounded p-4">
          <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
            <div>
              <h3 className="font-semibold text-sm text-zinc-900">Current Cooked Batches & Shelf-Life Countdown</h3>
              <p className="text-xs text-zinc-500">Live hot counter holding status</p>
            </div>
            <span className="text-xs text-emerald-700 font-medium">5 Active Batches</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-50 text-zinc-500 border-b border-border font-medium">
                <tr>
                  <th className="py-2 px-2.5">Batch Code</th>
                  <th className="py-2 px-2.5">Dish</th>
                  <th className="py-2 px-2.5">Prepared</th>
                  <th className="py-2 px-2.5">Expires</th>
                  <th className="py-2 px-2.5 font-mono">Time Left</th>
                  <th className="py-2 px-2.5 font-mono">Stock</th>
                  <th className="py-2 px-2.5">Discount Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {inventoryBatches.map((b, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50/60">
                    <td className="py-2.5 px-2.5 font-mono text-zinc-600">{b.batch_id}</td>
                    <td className="py-2.5 px-2.5 font-medium text-zinc-900">
                      {lang === 'bn' ? b.dish_bn : b.dish}
                    </td>
                    <td className="py-2.5 px-2.5 text-zinc-500">{b.prepared}</td>
                    <td className="py-2.5 px-2.5 text-zinc-500">{b.expiry}</td>
                    <td className="py-2.5 px-2.5 font-mono">
                      <span className={`px-1.5 py-0.5 rounded text-[11px] ${
                        parseFloat(b.hours_left) < 1.0 ? 'bg-rose-100 text-rose-800 font-bold' : 'bg-zinc-100 text-zinc-700'
                      }`}>
                        {b.hours_left}
                      </span>
                    </td>
                    <td className="py-2.5 px-2.5 font-mono font-medium text-zinc-800">
                      {b.stock} ptn
                    </td>
                    <td className="py-2.5 px-2.5">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                        b.status === 'discounted' 
                          ? 'bg-amber-50 text-amber-800 border-amber-300' 
                          : 'bg-zinc-100 text-zinc-700 border-zinc-200'
                      }`}>
                        {b.discount}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

