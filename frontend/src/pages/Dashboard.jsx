import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { 
  Trees, Sprout, Activity, AlertTriangle, MapPin, 
  Calendar, CheckCircle2, Search, PieChart as PieChartIcon,
  ChevronDown 
} from 'lucide-react';
import { getOrchardsRequest } from '../api/farming';
import { getDashboardAnalyticsRequest } from '../api/analytics';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

const COLORS = {
  healthy: '#39ff14',
  damaged: '#ff073a',
  total: '#9803b6ff'
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [orchards, setOrchards] = useState([]); // Store all available orchards
  const [selectedOrchardId, setSelectedOrchardId] = useState(null);
  const [orchard, setOrchard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  // 1. Initial load: Get all orchards
  useEffect(() => {
    async function fetchOrchards() {
      try {
        const res = await getOrchardsRequest();
        if (res.data && res.data.length > 0) {
          setOrchards(res.data);
          setSelectedOrchardId(res.data[0].id); // Default to the first one
        } else {
          setError("You don't have Orchards on your account!");
          setLoading(false);
        }
      } catch (err) {
        setError("Error: Unable to connect to the server.");
        setLoading(false);
      }
    }
    fetchOrchards();
  }, []);

  // 2. Load analytics whenever selectedOrchardId changes
  useEffect(() => {
    if (!selectedOrchardId) return;

    async function loadAnalytics() {
      setLoading(true);
      try {
        const current = orchards.find(o => o.id === selectedOrchardId);
        setOrchard(current);

        const analyticsRes = await getDashboardAnalyticsRequest(selectedOrchardId);
        setAnalytics(analyticsRes.data);
      } catch (err) {
        console.error("Error Loading Analytics:", err);
        setError("Error loading specific orchard data.");
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [selectedOrchardId, orchards]);

  const summary = analytics?.summary;
  const detections = analytics?.recent_detections || [];

  const totalHealthyApples = detections.reduce((sum, d) => sum + d.healthy_apples, 0);
  const totalDamagedApples = detections.reduce((sum, d) => sum + d.damaged_apples, 0);

  const appleDistribution = [
    { name: 'Healthy', value: totalHealthyApples, color: COLORS.healthy },
    { name: 'Damaged', value: totalDamagedApples, color: COLORS.damaged }
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/90 border border-apple-green/30 rounded-lg p-3 shadow-xl">
          <p className="text-white font-bold" style={{ color: payload[0].payload.color }}>
            {payload[0].name}: {payload[0].value}
          </p>
        </div>
      );
    }
    return null;
  };

  const ProgressBar = ({ value, max, color }) => {
    const percentage = (value / max) * 100;
    return (
      <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${color}`}
          style={{
            width: `${Math.min(percentage, 100)}%`,
            boxShadow: `0 0 8px ${color === 'bg-apple-green' ? '#39ff14' : '#ff073a'}`
          }}
        />
      </div>
    );
  };

  const stats = summary ? [
    { title: "Total Trees", value: orchard?.n_trees || "N/A", icon: Trees, color: "text-blue-400" },
    { title: "Detected Apples", value: summary.total_apples_found, icon: Sprout, color: "text-apple-green" },
    { title: "Avg Health%", value: `${summary.health_score_avg}%`, icon: Activity, color: summary.health_score_avg > 75 ? "text-apple-green" : "text-yellow-400" },
    { title: "Processed Images", value: summary.images_processed, icon: Search, color: "text-purple-400" },
  ] : [];

  if (loading && !analytics) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse"> Synchronizing data from the orchard...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* 1. Header with Orchard Selector */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-4xl font-black text-white mb-2 tracking-tight">
            {orchard?.name || "Select Orchard"}
          </h1>
          <div className="flex items-center gap-4 text-sm text-zinc-400 font-mono">
            <span className="flex items-center gap-1">
               <MapPin className="w-4 h-4 text-apple-green" /> {orchard?.location || "Unknown"}
            </span>
          </div>
        </div>

        {/* SELECTOR BUTTON */}
        <div className="relative group">
          <label className="block text-[10px] uppercase text-zinc-500 font-mono mb-1 ml-1">Switch Orchard</label>
          <div className="relative">
            <select 
              value={selectedOrchardId || ""}
              onChange={(e) => setSelectedOrchardId(Number(e.target.value))}
              className="appearance-none bg-zinc-900 border border-zinc-700 text-white py-2 pl-4 pr-10 rounded-lg focus:outline-none focus:border-apple-green transition-all cursor-pointer font-bold shadow-lg"
            >
              {orchards.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-apple-green pointer-events-none" />
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" /> {error}
        </div>
      )}

      {/* 2. KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <Card key={i} className="border-zinc-700/60 bg-black/60 hover:border-apple-green/40 transition-all">
            <div className="flex items-start justify-between">
                <div>
                  <p className="text-[12px] text-zinc-500 font-mono uppercase tracking-widest mb-1">{stat.title}</p>
                  <h3 className="text-3xl font-black text-white">{stat.value}</h3>
                </div>
                <div className={`p-2 rounded-lg bg-zinc-900/50 ${stat.color}`}>
                  <stat.icon className="w-6 h-6" />
                </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 3. Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Analytics Column */}
        <div className="space-y-6">
          <Card className="p-6 border-zinc-700 bg-black/40">
            <h3 className="text-white font-bold mb-6 flex items-center gap-2 text-lg">
              <PieChartIcon className="w-5 h-5 text-apple-green" />
              Apple Distribution
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={appleDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {appleDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-3 mt-6">
              <div className="p-3 bg-zinc-900/50 rounded-xl border border-apple-green/20">
                <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Healthy</p>
                <p className="text-2xl font-black text-apple-green">{totalHealthyApples}</p>
              </div>
              <div className="p-3 bg-zinc-900/50 rounded-xl border border-apple-red/20">
                <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Damaged</p>
                <p className="text-2xl font-black text-apple-red">{totalDamagedApples}</p>
              </div>
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-zinc-900 to-black border-zinc-700 p-6">
            <div className="mb-2 text-zinc-500 text-xs font-mono uppercase tracking-widest">Global Health Index</div>
            <div className="text-5xl font-black text-white mb-4">
              {summary?.health_score_avg.toFixed(1)}%
            </div>
            <ProgressBar
              value={summary?.health_score_avg || 0}
              max={100}
              color={summary?.health_score_avg >= 75 ? 'bg-apple-green' : 'bg-yellow-500'}
            />
            <div className={`text-sm font-bold flex items-center justify-center gap-2 mt-6 ${summary?.health_score_avg >= 75 ? 'text-apple-green' : 'text-yellow-400'}`}>
              <CheckCircle2 className="w-4 h-4" /> 
              {summary?.health_score_avg >= 75 ? 'OPTIMAL CONDITIONS' : 'ATTENTION REQUIRED'}
            </div>
          </Card>
        </div>

        {/* RECENT ACTIVITY TABLE - ENHANCED */}
        <div className="lg:col-span-2">
            <Card className="p-0 overflow-hidden border-zinc-700 bg-cyber-dark">
                <div className="p-5 border-b border-zinc-700 bg-black/40 flex justify-between items-center">
                    <h3 className="font-black text-white text-xl flex items-center gap-2">
                        <Activity className="w-5 h-5 text-apple-green" /> RECENT ACTIVITY LOG
                    </h3>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="text-xs text-zinc-500 uppercase bg-black/60 font-mono tracking-tighter">
                            <tr>
                                <th className="px-6 py-4">Timestamp / ID</th>
                                <th className="px-6 py-4">Tree Code</th>
                                <th className="px-6 py-4 text-center">Health %</th>
                                <th className="px-6 py-4 text-center">Apples (H / D)</th>
                                <th className="px-6 py-4 text-center font-bold text-apple-green">Total</th>
                                <th className="px-6 py-4 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {detections.map((item) => (
                                <tr key={item.prediction_id} className="hover:bg-apple-green/5 transition-all group">
                                    {/* FIXED DATE DISPLAY */}
                                    <td className="px-6 py-5">
                                        <div className="text-white font-black text-lg leading-none mb-1">
                                            {(() => {
                                                const date = new Date(item.updated_at);
                                                return !isNaN(date.getTime())
                                                    ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                                                    : 'N/A';
                                            })()}
                                        </div>
                                        <div className="text-apple-green font-mono text-sm opacity-80">
                                            {(() => {
                                                const date = new Date(item.updated_at);
                                                return !isNaN(date.getTime())
                                                    ? date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                                                    : '--:--:--';
                                            })()}
                                        </div>
                                        <div className="text-[16px] text-zinc-600 font-mono mt-1">#ID_{item.prediction_id}</div>
                                    </td>

                                    <td className="px-6 py-5">
                                        <span className="text-zinc-300 font-bold text-xl">{item.tree_code}</span>
                                    </td>

                                    <td className="px-6 py-5 text-center">
                                        <div className={`inline-block px-3 py-1 rounded-full text-sm font-black border ${
                                            item.health_index >= 80 ? 'bg-apple-green/10 text-apple-green border-apple-green/30' : 
                                            item.health_index >= 50 ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30' : 'bg-red-500/10 text-red-500 border-red-500/30'
                                            
                                        }`}>
                                            {item.health_index.toFixed(0)}%
                                        </div>
                                    </td>

                                    {/* APPLES (H/D) COLUMN */}
                                    <td className="px-6 py-5 text-center font-mono">
                                        <span className="text-apple-green font-bold text-lg">{item.healthy_apples}</span>
                                        <span className="text-zinc-600 mx-2">/</span>
                                        <span className="text-apple-red font-bold text-lg">{item.damaged_apples}</span>
                                    </td>

                                    {/* NEW TOTAL COLUMN */}
                                    <td className="px-6 py-5 text-center">
                                        <div className="text-white text-2xl font-black tracking-tighter">
                                            {item.healthy_apples + item.damaged_apples}
                                        </div>
                                    </td>

                                    <td className="px-6 py-5 text-center">
                                        {item.damaged_apples === 0 ? (
                                            <CheckCircle2 className="w-6 h-6 text-apple-green mx-auto drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
                                        ) : (
                                            <AlertTriangle className="w-6 h-6 text-yellow-500 mx-auto" />
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>

      </div>
    </div>
  );
}