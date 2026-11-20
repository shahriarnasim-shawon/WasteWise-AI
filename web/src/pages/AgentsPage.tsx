import React, { useState, useEffect } from 'react';
import { translations } from '../i18n';
import { Language, DailyForecastItem, OrderItem, DiscountOfferItem, AgentLogItem } from '../types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend 
} from 'recharts';
import { 
  Cpu, Check, Edit3, Tag, Clock, Play, ShieldAlert, Sparkles, MessageSquare 
} from 'lucide-react';

interface AgentsPageProps {
  lang: Language;
}

export const AgentsPage: React.FC<AgentsPageProps> = ({ lang }) => {
  const t = translations[lang];

  const [forecasts, setForecasts] = useState<DailyForecastItem[]>([]);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [discounts, setDiscounts] = useState<DiscountOfferItem[]>([]);
  const [logs, setLogs] = useState<AgentLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Override modal state
  const [overrideOrderId, setOverrideOrderId] = useState<number | null>(null);
  const [overrideValue, setOverrideValue] = useState<number>(0);
  const [overrideReason, setOverrideReason] = useState<string>('');

  const fetchAgentData = async () => {
    setIsLoading(true);
    try {
      const [fRes, oRes, dRes, lRes] = await Promise.all([
        fetch('/api/agents/forecasts?meal_period=lunch'),
        fetch('/api/agents/orders?meal_period=lunch'),
        fetch('/api/agents/discounts'),
        fetch('/api/agents/logs?limit=25')
      ]);

      const fData = await fRes.json();
      const oData = await oRes.json();
      const dData = await dRes.json();
      const lData = await lRes.json();

      if (fData.forecasts) setForecasts(fData.forecasts);
      if (oData.orders) setOrders(oData.orders);
      if (dData.offers) setDiscounts(dData.offers);
      if (lData.logs) setLogs(lData.logs);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentData();
  }, []);

  const handleAcceptOrder = async (orderId: number) => {
    try {
      await fetch(`/api/agents/orders/${orderId}/accept`, { method: 'POST' });
      fetchAgentData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveOverride = async () => {
    if (!overrideOrderId) return;
    try {
      await fetch(`/api/agents/orders/${overrideOrderId}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_portions: overrideValue,
          override_reason: overrideReason || 'Manual chef adjustment based on physical kitchen capacity.'
        })
      });
      setOverrideOrderId(null);
      fetchAgentData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTriggerCycle = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/agents/run_cycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meal_period: 'lunch',
          weather_flag: 'rain',
          event_flag: 'friday_prayer'
        })
      });
      fetchAgentData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Forecast chart data
  const forecastChartData = (forecasts.length > 0 ? forecasts : [
    { food_class: 'rice', forecast_portions: 380, lower_bound: 340, upper_bound: 420 },
    { food_class: 'dal', forecast_portions: 310, lower_bound: 280, upper_bound: 350 },
    { food_class: 'bhuna_khichuri', forecast_portions: 165, lower_bound: 140, upper_bound: 195 },
    { food_class: 'chicken_curry', forecast_portions: 245, lower_bound: 215, upper_bound: 280 },
    { food_class: 'fish_curry', forecast_portions: 155, lower_bound: 130, upper_bound: 180 },
    { food_class: 'vegetable', forecast_portions: 180, lower_bound: 155, upper_bound: 210 },
  ]).map(f => ({
    name: f.food_class.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    Forecast: f.forecast_portions,
    LowerCI: f.lower_bound,
    UpperCI: f.upper_bound
  }));

  return (
    <div className="space-y-4">
      
      {/* Top Controls Header */}
      <div className="bg-white border border-border p-3.5 rounded flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-primary" />
            <span>Autonomous Canteen Predictive Agents</span>
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            4 coordinated agents: Demand Forecast • Kitchen Ordering • Dynamic Discount • Waste Routing
          </p>
        </div>

        <button
          onClick={handleTriggerCycle}
          disabled={isLoading}
          className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded hover:bg-primary-hover transition-colors flex items-center space-x-1"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{isLoading ? 'Running Cycle...' : 'Run Agents Cycle (Trigger)'}</span>
        </button>
      </div>

      {/* Grid: Forecast Chart & Today's Offers Board */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Demand Forecast Chart */}
        <div className="bg-white border border-border rounded p-4">
          <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
            <div>
              <h3 className="font-semibold text-sm text-zinc-900">DemandForecastAgent Predictions</h3>
              <p className="text-xs text-zinc-500">Lunch Portions with 90% Confidence Interval</p>
            </div>
            <span className="text-[11px] font-mono text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded">
              Weather: Rain (+35% Khichuri)
            </span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={forecastChartData} margin={{ top: 10, right: 10, left: -15, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#71717a' }} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#71717a' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e4e4e7', fontSize: '11px' }}
                  formatter={(val: any) => [`${val} portions`, '']}
                />
                <Bar dataKey="Forecast" fill="#1e3a2b" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Today's Offers Dynamic Discount Board */}
        <div className="bg-white border border-border rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
              <div>
                <h3 className="font-semibold text-sm text-zinc-900">Today's Offers (Dynamic Discount Board)</h3>
                <p className="text-xs text-zinc-500">Auto-published discounts on near-expiry batches</p>
              </div>
              <span className="text-xs font-mono text-terracotta font-medium flex items-center">
                <Tag className="w-3.5 h-3.5 mr-1" />
                <span>Live Markdown Board</span>
              </span>
            </div>

            <div className="space-y-2.5">
              {(discounts.length > 0 ? discounts : [
                {
                  id: 1,
                  food_class: 'bhuna_khichuri',
                  discount_tier: 3,
                  discount_percent: 35.0,
                  original_price_bdt: 80.0,
                  discounted_price_bdt: 52.0,
                  reason: 'Near expiry: 0.8h remaining with 32 portions unsold.',
                  active_until: '03:30 PM'
                },
                {
                  id: 2,
                  food_class: 'rice',
                  discount_tier: 2,
                  discount_percent: 20.0,
                  original_price_bdt: 35.0,
                  discounted_price_bdt: 28.0,
                  reason: 'Surplus clearance: 65 portions remaining before late afternoon rush.',
                  active_until: '04:00 PM'
                }
              ]).map((off) => (
                <div key={off.id} className="p-3 bg-zinc-50 border border-border rounded text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-zinc-900 text-sm">
                      {off.food_class.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-terracotta text-white font-mono font-bold text-xs">
                      {off.discount_percent}% OFF
                    </span>
                  </div>

                  <div className="flex justify-between items-center mt-2 text-xs">
                    <div className="flex items-center space-x-2 font-mono">
                      <span className="line-through text-zinc-400">৳{off.original_price_bdt}</span>
                      <span className="font-bold text-terracotta text-sm">৳{off.discounted_price_bdt}</span>
                      <span className="text-[10px] text-zinc-400 bg-zinc-200/60 px-1.5 py-0.5 rounded">
                        Floor Guardrail Active
                      </span>
                    </div>
                    <span className="text-[11px] text-zinc-500 font-mono flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      Expires: {off.active_until.slice(-8, -3) || off.active_until}
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-600 mt-1.5 pt-1.5 border-t border-zinc-200 leading-tight">
                    {off.reason}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="text-[11px] text-zinc-500 bg-zinc-100 p-2 rounded mt-3 flex items-center">
            <ShieldAlert className="w-3.5 h-3.5 text-zinc-600 mr-1.5 flex-shrink-0" />
            <span>Unit cost floor protection active. Dynamic discount cannot fall below ingredient cost.</span>
          </div>
        </div>
      </div>

      {/* Grid: Kitchen Orders (Accept/Override) & Live Agent Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Kitchen Order Recommendations */}
        <div className="bg-white border border-border rounded p-4">
          <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
            <div>
              <h3 className="font-semibold text-sm text-zinc-900">Kitchen Prep Recommendations (OrderingAgent)</h3>
              <p className="text-xs text-zinc-500">Forecast minus current usable stock + safety stock</p>
            </div>
            <span className="text-xs font-mono text-zinc-500">Lunch Shift</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-50 text-zinc-500 border-b border-border font-medium">
                <tr>
                  <th className="py-2 px-2.5">Dish</th>
                  <th className="py-2 px-2.5 font-mono">Forecast</th>
                  <th className="py-2 px-2.5 font-mono">Stock</th>
                  <th className="py-2 px-2.5 font-mono">Order</th>
                  <th className="py-2 px-2.5">Status</th>
                  <th className="py-2 px-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(orders.length > 0 ? orders : [
                  { id: 1, food_class: 'rice', recommended_portions: 315, current_stock: 65, safety_stock: 25, status: 'pending' },
                  { id: 2, food_class: 'bhuna_khichuri', recommended_portions: 135, current_stock: 32, safety_stock: 12, status: 'accepted' },
                  { id: 3, food_class: 'chicken_curry', recommended_portions: 200, current_stock: 45, safety_stock: 16, status: 'pending' },
                  { id: 4, food_class: 'fish_curry', recommended_portions: 130, current_stock: 28, safety_stock: 10, status: 'pending' },
                ]).map((ord: any) => (
                  <tr key={ord.id} className="hover:bg-zinc-50/60">
                    <td className="py-2.5 px-2.5 font-medium text-zinc-900">
                      {ord.food_class.replace('_', ' ').toUpperCase()}
                    </td>
                    <td className="py-2.5 px-2.5 font-mono text-zinc-600">
                      {ord.recommended_portions + ord.current_stock - ord.safety_stock}
                    </td>
                    <td className="py-2.5 px-2.5 font-mono text-zinc-600">{ord.current_stock}</td>
                    <td className="py-2.5 px-2.5 font-mono font-bold text-zinc-900">{ord.recommended_portions} ptn</td>
                    <td className="py-2.5 px-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                        ord.status === 'accepted' 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : ord.status === 'overridden' 
                            ? 'bg-amber-100 text-amber-800' 
                            : 'bg-zinc-100 text-zinc-700'
                      }`}>
                        {ord.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-2.5 text-right">
                      {ord.status === 'pending' ? (
                        <div className="flex items-center justify-end space-x-1">
                          <button
                            onClick={() => handleAcceptOrder(ord.id)}
                            className="p-1 text-emerald-700 hover:bg-emerald-50 rounded"
                            title="Accept Recommendation"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => {
                              setOverrideOrderId(ord.id);
                              setOverrideValue(ord.recommended_portions);
                            }}
                            className="p-1 text-zinc-600 hover:bg-zinc-100 rounded"
                            title="Override Quantity"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <span className="text-[10px] text-zinc-400">Locked</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Explainable Agent Log */}
        <div className="bg-white border border-border rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
              <div>
                <h3 className="font-semibold text-sm text-zinc-900">Agent Reasoning Audit Log</h3>
                <p className="text-xs text-zinc-500">Transparent human-readable decision log</p>
              </div>
              <span className="text-xs font-mono text-zinc-400">Audit Trail</span>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {(logs.length > 0 ? logs : [
                {
                  id: 1,
                  timestamp: '12:45 PM',
                  agent_name: 'DynamicDiscountAgent',
                  action: 'PUBLISH_DYNAMIC_DISCOUNT',
                  rationale: 'Applied Tier 3 (35% off) to Bhuna Khichuri [Batch BATCH-KC-204]. Original: 80.0 BDT, New: 52.0 BDT (Floor Guardrail: 45.0 BDT). Rationale: Near expiry: 0.8h remaining.'
                },
                {
                  id: 2,
                  timestamp: '12:30 PM',
                  agent_name: 'AgentOrchestrator',
                  action: 'RESOLVE_ORDER_SURPLUS_CONFLICT',
                  rationale: 'Resolved 1 kitchen prep conflict: downscaled Khichuri orders by 32 portions to prioritize clearance of existing discounted surplus.'
                },
                {
                  id: 3,
                  timestamp: '12:15 PM',
                  agent_name: 'WasteCollectionAgent',
                  action: 'SCHEDULE_WASTE_PICKUP',
                  rationale: 'Scheduled collection manifest WW-COMP-20261115-A109 for Organic Compost. Bin reached 85.7% of 35 kg capacity.'
                },
                {
                  id: 4,
                  timestamp: '11:00 AM',
                  agent_name: 'DemandForecastAgent',
                  action: 'GENERATE_DAILY_FORECAST',
                  rationale: 'Forecasted 165 portions of Bhuna Khichuri for Lunch on Friday. Weather modifier (rain) +35% applied.'
                }
              ]).map((log: any) => (
                <div key={log.id} className="p-2.5 bg-zinc-50 border border-border rounded text-xs">
                  <div className="flex items-center justify-between text-[11px] text-zinc-500 mb-1">
                    <span className="font-semibold text-primary font-mono">{log.agent_name}</span>
                    <span className="font-mono text-zinc-400">{log.timestamp.slice(-8, -3) || log.timestamp}</span>
                  </div>
                  <div className="text-[10px] font-mono text-zinc-700 font-semibold mb-1">
                    [{log.action}]
                  </div>
                  <p className="text-[11px] text-zinc-600 leading-relaxed font-sans">
                    {log.rationale}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Override Modal */}
      {overrideOrderId && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded p-4 max-w-sm w-full border border-border shadow-xl text-xs space-y-3">
            <h4 className="font-semibold text-sm text-zinc-900">Override Order Recommendation</h4>
            <div>
              <label className="text-zinc-600 text-[11px]">New Portions Quantity:</label>
              <input
                type="number"
                value={overrideValue}
                onChange={(e) => setOverrideValue(Number(e.target.value))}
                className="w-full mt-1 border border-border rounded p-1.5 font-mono text-sm"
              />
            </div>
            <div>
              <label className="text-zinc-600 text-[11px]">Chef Override Reason:</label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="e.g. Expecting 50 visiting delegates from chemical engineering dept."
                className="w-full mt-1 border border-border rounded p-1.5 text-xs h-16"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2 border-t border-border">
              <button
                onClick={() => setOverrideOrderId(null)}
                className="px-3 py-1 bg-zinc-100 text-zinc-700 rounded hover:bg-zinc-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveOverride}
                className="px-3 py-1 bg-primary text-white rounded hover:bg-primary-hover font-medium"
              >
                Save Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

