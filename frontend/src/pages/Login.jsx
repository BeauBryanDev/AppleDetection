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
  const [orchards, setOrchards] = useState([]); 
  const [selectedOrchardId, setSelectedOrchardId] = useState(null);
  const [orchard, setOrchard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  // 1. Initial load: Fetch all orchards
  useEffect(() => {
    async function fetchOrchards() {
      try {
        const res = await getOrchardsRequest();
        if (res.data && res.data.length > 0) {
          setOrchards(res.data);
          setSelectedOrchardId(res.data[0].id); 
        } else {
          setError("No orchards found!");
          setLoading(false);
        }
      } catch (err) {
        setError("Connection error.");
        setLoading(false);
      }
    }
    fetchOrchards();
  }, []);

  // 2. Refresh analytics when selectedOrchardId changes
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
        setError("Error loading orchard analytics.");
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [selectedOrchardId, orchards]);

  const summary = analytics?.summary;
  const detections = analytics?.recent_detections || [];

  const totalHealthy = detections.reduce((sum, d) => sum + d.healthy_apples, 0);
  const totalDamaged = detections.reduce((sum, d) => sum + d.damaged_apples, 0);

  const appleData = [
    { name: 'Healthy', value: totalHealthy, color: COLORS.healthy },
    { name: 'Damaged', value: totalDamaged, color: COLORS.damaged }
  ];

  const stats = summary ? [
    { title: "Total Trees", value: orchard?.n_trees || "N/A", icon: Trees, color: "text-blue-400" },
    { title: "Apples Detected", value: summary.total_apples_found, icon: Sprout, color: "text-apple-green" },
    { title: "Avg Health%", value: `${summary.health_score_avg}%`, icon: Activity, color: summary.health_score_avg > 75 ? "text-apple-green" : "text-yellow-400" },
    { title: "Processed Images", value: summary.images_processed, icon: Search, color: "text-purple-400" },
  ] : [];

  if (loading && !analytics) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse text-xl">Syncing Data...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500 p-4">
      
      {/* 1. Header with Switcher */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-6 border-b border-zinc-800 pb-8">
        <div>
          <h1 className="text-5xl font-black text-white mb-2 tracking-tighter">
            {orchard?.name || "Loading..."}
          </h1>
          <div className="flex items-center gap-4 text-base text-zinc-400 font-mono">
            <span className="flex items-center gap-1">
               <MapPin className="w-5 h-5 text-apple-green" /> {orchard?.location}
            </span>
          </div>
        </div>

        <div className="bg-zinc-900 p-1 rounded-xl border border-zinc-800 flex items-center shadow-2xl">
          <label className="px-4 text-xs font-black text-zinc-500 uppercase font-mono border-r border-zinc-800">Orchard</label>
          <select 
            value={selectedOrchardId || ""}
            onChange={(e) => setSelectedOrchardId(Number(e.target.value))}
            className="bg-transparent text-white py-3 px-4 focus:outline-none font-bold cursor-pointer text-lg"
          >
            {orchards.map((o) => (
              <option key={o.id} value={o.id} className="bg-zinc-900">{o.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 2. KPI Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <Card key={i} className="border-zinc-700 bg-black/60 hover:border-apple-green/50 transition-all p-6">
            <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-zinc-500 font-mono uppercase tracking-widest mb-2">{stat.title}</p>
                  <h3 className="text-4xl font-black text-white tracking-tighter">{stat.value}</h3>
                </div>
                <div className={`p-3 rounded-xl bg-zinc-900 ${stat.color} shadow-lg shadow-black/50`}>
                  <stat.icon className="w-8 h-8" />
                </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 3. Main Data Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Analytics Column */}
        <div className="space-y-8">
          <Card className="p-8 border-zinc-700 bg-black/40 shadow-2xl">
            <h3 className="text-xl font-black text-white mb-8 flex items-center gap-3">
              <PieChartIcon className="w-6 h-6 text-apple-green" /> DISTRIBUTION
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={appleData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} paddingAngle={8} dataKey="value">
                  {appleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-4 mt-8">
              <div className="p-4 bg-zinc-900/80 rounded-2xl border-l-4 border-apple-green">
                <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Healthy</p>
                <p className="text-3xl font-black text-apple-green">{totalHealthy}</p>
              </div>
              <div className="p-4 bg-zinc-900/80 rounded-2xl border-l-4 border-apple-red">
                <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Damaged</p>
                <p className="text-3xl font-black text-apple-red">{totalDamaged}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* RECENT ACTIVITY TABLE */}
        <div className="lg:col-span-2">
            <Card className="p-0 overflow-hidden border-zinc-700 bg-cyber-dark shadow-2xl">
                <div className="p-6 border-b border-zinc-700 bg-black/40 flex justify-between items-center">
                    <h3 className="font-black text-white text-2xl flex items-center gap-3">
                        <Activity className="w-6 h-6 text-apple-green" /> ACTIVITY LOG
                    </h3>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="text-[11px] text-zinc-500 uppercase bg-black/60 font-mono tracking-widest">
                            <tr>
                                <th className="px-8 py-5">TIMESTAMP</th>
                                <th className="px-8 py-5">TREE CODE</th>
                                <th className="px-8 py-5 text-center">HEALTH</th>
                                <th className="px-8 py-5 text-center">H / D</th>
                                <th className="px-8 py-5 text-center text-apple-green font-black">TOTAL</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {detections.map((item) => {
                                // REPAIRED DATE LOGIC
                                const dateObj = item.updated_at ? new Date(item.updated_at) : null;
                                const isValid = dateObj && !isNaN(dateObj.getTime());

                                return (
                                    <tr key={item.prediction_id} className="hover:bg-apple-green/5 transition-all">
                                        <td className="px-8 py-6">
                                            <div className="text-white font-black text-xl mb-1">
                                                {isValid ? dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : "---"}
                                            </div>
                                            <div className="text-apple-green font-mono text-sm">
                                                {isValid ? dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : "---"}
                                            </div>
                                        </td>
                                        
                                        <td className="px-8 py-6">
                                            <span className="text-zinc-300 font-black text-xl uppercase tracking-tighter">
                                                {item.tree_code}
                                            </span>
                                        </td>

                                        <td className="px-8 py-6 text-center">
                                            <div className={`inline-block px-4 py-1.5 rounded-full text-sm font-black border ${
                                                item.health_index >= 80 ? 'bg-apple-green/10 text-apple-green border-apple-green/30' : 
                                                'bg-red-500/10 text-red-500 border-red-500/30'
                                            }`}>
                                                {item.health_index?.toFixed(0)}%
                                            </div>
                                        </td>

                                        <td className="px-8 py-6 text-center font-mono">
                                            <span className="text-apple-green font-black text-2xl">{item.healthy_apples}</span>
                                            <span className="text-zinc-700 mx-3 text-xl">/</span>
                                            <span className="text-apple-red font-black text-2xl">{item.damaged_apples}</span>
                                        </td>

                                        <td className="px-8 py-6 text-center">
                                            <div className="text-white text-4xl font-black tracking-tighter">
                                                {item.healthy_apples + item.damaged_apples}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>

      </div>
    </div>
  );
}