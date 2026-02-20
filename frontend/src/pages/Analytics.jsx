import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  BarChart3,
  TrendingUp,
  Trees,
  Sprout,
  Activity,
  AlertTriangle,
  ChevronDown,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  RadialBarChart,
  RadialBar
} from 'recharts';
import {
  getUserSummaryRequest,
  getTreesSummaryRequest,
  getHealthTrendRequest
} from '../api/analytics';
import { getOrchardsRequest } from '../api/farming';

// Cyberpunk color scheme
const COLORS = {
  healthy: '#39ff14',
  damaged: '#ff073a',
  total: '#00d4ff',
  background: '#050505',
  grid: '#1a1a1a'
};

const PIE_COLORS = ['#39ff14', '#ff073a', '#00d4ff', '#ff6b35', '#f7b731'];

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [userSummary, setUserSummary] = useState(null);
  const [orchards, setOrchards] = useState([]);
  const [selectedOrchard, setSelectedOrchard] = useState(null);
  const [treesSummary, setTreesSummary] = useState(null);
  const [healthTrend, setHealthTrend] = useState(null);
  const [showOrchardDropdown, setShowOrchardDropdown] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedOrchard) {
      loadOrchardAnalytics(selectedOrchard.id);
    }
  }, [selectedOrchard]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryRes, orchardsRes] = await Promise.all([
        getUserSummaryRequest(),
        getOrchardsRequest()
      ]);

      setUserSummary(summaryRes.data);
      setOrchards(orchardsRes.data);

      if (orchardsRes.data.length > 0) {
        setSelectedOrchard(orchardsRes.data[0]);
      }
    } catch (err) {
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadOrchardAnalytics = async (orchardId) => {
    try {
      const [treesRes, trendRes] = await Promise.all([
        getTreesSummaryRequest(orchardId),
        getHealthTrendRequest(orchardId, 15)
      ]);

      setTreesSummary(treesRes.data);
      setHealthTrend(trendRes.data);
    } catch (err) {
      console.error('Error loading orchard analytics:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse">Analizando datos...</p>
      </div>
    );
  }

  const globalStats = userSummary?.global_summary || {};

  // Prepare data for global pie chart (total apples across all orchards)
  const totalHealthy = userSummary?.orchards?.reduce((sum, o) => {
    // Estimate healthy apples from total and health percentage
    return sum + (o.apples_detected * (o.avg_health / 100));
  }, 0) || 0;

  const totalDamaged = (globalStats.total_apples_detected || 0) - totalHealthy;

  const globalAppleData = [
    { name: 'Sanas', value: Math.round(totalHealthy), color: COLORS.healthy },
    { name: 'Dañadas', value: Math.round(totalDamaged), color: COLORS.damaged }
  ];

  // Prepare data for orchard comparison bar chart
  const orchardComparisonData = userSummary?.orchards?.map(o => ({
    name: o.orchard_name.length > 15 ? o.orchard_name.substring(0, 15) + '...' : o.orchard_name,
    Manzanas: o.apples_detected,
    Salud: o.avg_health
  })) || [];

  // Prepare health trend data for line chart
  const trendChartData = healthTrend?.trend?.map(point => ({
    fecha: new Date(point.timestamp).toLocaleDateString('es-ES', { month: 'short', day: 'numeric' }),
    'Índice de Salud': point.health_index
  })) || [];

  // Progress bar component
  const ProgressBar = ({ label, value, max, color, showPercentage = false }) => {
    const percentage = (value / max) * 100;
    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-zinc-400 font-mono">{label}</span>
          <span className="text-sm font-bold text-white">
            {showPercentage ? `${value.toFixed(1)}%` : value}
            {!showPercentage && <span className="text-zinc-600 ml-1">/ {max}</span>}
          </span>
        </div>
        <div className="w-full bg-zinc-900 rounded-full h-3 overflow-hidden border border-zinc-800">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-out ${color} shadow-lg`}
            style={{
              width: `${Math.min(percentage, 100)}%`,
              boxShadow: `0 0 10px ${color === 'bg-apple-green' ? '#39ff14' : color === 'bg-apple-red' ? '#ff073a' : '#00d4ff'}`
            }}
          />
        </div>
      </div>
    );
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/90 border border-apple-green/30 rounded-lg p-3 shadow-xl">
          <p className="text-zinc-400 text-xs font-mono mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-white font-bold text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-5 sm:space-y-6 lg:space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 flex items-center gap-2 sm:gap-3">
            <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8 text-apple-green" />
            Analytics Dashboard
          </h1>
          <p className="text-zinc-500 text-sm font-mono">
            Usuario: {userSummary?.user_name} | Rol: {userSummary?.user_role}
          </p>
        </div>
      </div>

      {/* Global Stats */}
      <div>
        <h2 className="text-white font-bold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-apple-green" />
          Resumen Global
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <Card className="border-zinc-800 bg-black/40 hover:bg-zinc-900/40 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                  Huertos Totales
                </p>
                <h3 className="text-2xl font-bold text-white">{globalStats.total_orchards || 0}</h3>
              </div>
              <div className="p-2 rounded-lg bg-zinc-900/50 text-blue-400">
                <Trees className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="border-zinc-800 bg-black/40 hover:bg-zinc-900/40 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                  Árboles Totales
                </p>
                <h3 className="text-2xl font-bold text-white">{globalStats.total_trees || 0}</h3>
              </div>
              <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-green">
                <Sprout className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="border-zinc-800 bg-black/40 hover:bg-zinc-900/40 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                  Imágenes Procesadas
                </p>
                <h3 className="text-2xl font-bold text-white">{globalStats.total_images_processed || 0}</h3>
              </div>
              <div className="p-2 rounded-lg bg-zinc-900/50 text-purple-400">
                <Activity className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="border-zinc-800 bg-black/40 hover:bg-zinc-900/40 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                  Manzanas Detectadas
                </p>
                <h3 className="text-2xl font-bold text-white">{globalStats.total_apples_detected || 0}</h3>
              </div>
              <div className="p-2 rounded-lg bg-zinc-900/50 text-yellow-400">
                <Sprout className="w-5 h-5" />
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6 lg:gap-8">
        {/* Global Apple Distribution Pie Chart */}
        <Card className="p-4 sm:p-6 border-zinc-800 bg-gradient-to-br from-zinc-900/90 to-black">
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <PieChartIcon className="w-5 h-5 text-apple-green" />
            Distribución Global de Manzanas
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={globalAppleData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {globalAppleData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="text-center p-3 bg-apple-green/10 rounded-lg border border-apple-green/30">
              <p className="text-xs text-zinc-400 mb-1">Sanas</p>
              <p className="text-2xl font-bold text-apple-green">{Math.round(totalHealthy)}</p>
            </div>
            <div className="text-center p-3 bg-apple-red/10 rounded-lg border border-apple-red/30">
              <p className="text-xs text-zinc-400 mb-1">Dañadas</p>
              <p className="text-2xl font-bold text-apple-red">{Math.round(totalDamaged)}</p>
            </div>
          </div>
        </Card>

        {/* Orchard Comparison Bar Chart */}
        <Card className="p-4 sm:p-6 border-zinc-800 bg-gradient-to-br from-zinc-900/90 to-black">
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-apple-green" />
            Comparación por Huerto
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={orchardComparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis
                dataKey="name"
                stroke="#666"
                tick={{ fill: '#999', fontSize: 11 }}
                angle={-15}
                textAnchor="end"
                height={60}
              />
              <YAxis stroke="#666" tick={{ fill: '#999' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="Manzanas" fill={COLORS.total} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Orchards Progress Bars */}
      <Card className="p-6 border-zinc-800 bg-cyber-dark">
        <h3 className="text-white font-bold mb-6 flex items-center gap-2">
          <Trees className="w-5 h-5 text-apple-green" />
          Métricas por Huerto
        </h3>
        <div className="space-y-5 sm:space-y-6">
          {userSummary?.orchards?.map((orchard) => (
            <div key={orchard.orchard_id} className="p-4 rounded-lg bg-zinc-900/30 border border-zinc-800">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 mb-4">
                <h4 className="text-white font-medium break-words">{orchard.orchard_name}</h4>
                <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-1 rounded">
                  {orchard.location}
                </span>
              </div>
              <div className="space-y-3">
                <ProgressBar
                  label="Árboles"
                  value={orchard.n_trees}
                  max={Math.max(...(userSummary.orchards.map(o => o.n_trees)), 10)}
                  color="bg-blue-500"
                />
                <ProgressBar
                  label="Manzanas Detectadas"
                  value={orchard.apples_detected}
                  max={Math.max(...(userSummary.orchards.map(o => o.apples_detected)), 10)}
                  color="bg-apple-green"
                />
                <ProgressBar
                  label="Índice de Salud"
                  value={orchard.avg_health}
                  max={100}
                  color={orchard.avg_health >= 80 ? 'bg-apple-green' : orchard.avg_health >= 50 ? 'bg-yellow-500' : 'bg-apple-red'}
                  showPercentage
                />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Orchard Details Section */}
      {selectedOrchard && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6 lg:gap-8">
          {/* Health Trend Line Chart */}
          <div className="lg:col-span-2">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 mb-4">
              <h2 className="text-white font-bold flex items-center gap-2 break-words">
                <LineChartIcon className="w-5 h-5 text-apple-green" />
                Tendencia de Salud - {selectedOrchard.name}
              </h2>
              {/* Orchard Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowOrchardDropdown(!showOrchardDropdown)}
                  className="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white text-sm flex items-center gap-2 hover:bg-zinc-800 hover:border-apple-green/30 transition-all"
                >
                  {selectedOrchard.name}
                  <ChevronDown className="w-4 h-4" />
                </button>
                {showOrchardDropdown && (
                  <div className="absolute right-0 mt-2 w-64 bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
                    {orchards.map((orchard) => (
                      <button
                        key={orchard.id}
                        onClick={() => {
                          setSelectedOrchard(orchard);
                          setShowOrchardDropdown(false);
                        }}
                        className={`w-full px-4 py-2 text-left text-white hover:bg-zinc-800 text-sm transition-colors ${
                          selectedOrchard.id === orchard.id ? 'bg-zinc-800 border-l-2 border-apple-green' : ''
                        }`}
                      >
                        {orchard.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <Card className="p-4 sm:p-6 border-zinc-800 bg-gradient-to-br from-zinc-900/90 to-black">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trendChartData}>
                  <defs>
                    <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.healthy} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={COLORS.healthy} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                  <XAxis
                    dataKey="fecha"
                    stroke="#666"
                    tick={{ fill: '#999', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#666"
                    tick={{ fill: '#999' }}
                    domain={[0, 100]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="Índice de Salud"
                    stroke={COLORS.healthy}
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorHealth)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Trees Summary */}
          <div>
            <h2 className="text-white font-bold mb-4 flex items-center gap-2">
              <Sprout className="w-5 h-5 text-apple-green" />
              Análisis por Árbol
            </h2>

            <Card className="p-4 border-zinc-800 bg-cyber-dark max-h-[500px] overflow-y-auto custom-scrollbar">
              <div className="space-y-2">
                {treesSummary?.trees?.map((tree) => (
                  <div
                    key={tree.tree_id}
                    className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-apple-green/30 transition-all hover:shadow-lg hover:shadow-apple-green/10"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="text-white font-medium">#{tree.tree_code}</h4>
                        <p className="text-xs text-zinc-500">{tree.tree_type || 'Sin tipo'}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          tree.avg_health_index >= 80
                            ? 'bg-apple-green/10 text-apple-green border border-apple-green/30'
                            : tree.avg_health_index >= 50
                            ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/30'
                            : 'bg-red-500/10 text-red-500 border border-red-500/30'
                        }`}
                      >
                        {tree.avg_health_index.toFixed(1)}%
                      </span>
                    </div>
                    <div className="space-y-2">
                      <ProgressBar
                        label="Imágenes"
                        value={tree.total_images}
                        max={Math.max(...(treesSummary.trees.map(t => t.total_images)), 5)}
                        color="bg-purple-500"
                      />
                      <ProgressBar
                        label="Manzanas"
                        value={tree.total_apples_detected}
                        max={Math.max(...(treesSummary.trees.map(t => t.total_apples_detected)), 10)}
                        color="bg-apple-green"
                      />
                    </div>
                  </div>
                ))}
                {(!treesSummary?.trees || treesSummary.trees.length === 0) && (
                  <p className="text-center text-zinc-600 py-8">No hay datos de árboles</p>
                )}
              </div>
            </Card>
          </div>

          {/* Tree Health Radial Chart */}
          <div>
            <h2 className="text-white font-bold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-apple-green" />
              Salud Promedio por Árbol
            </h2>
            <Card className="p-4 sm:p-6 border-zinc-800 bg-gradient-to-br from-zinc-900/90 to-black">
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={treesSummary?.trees?.slice(0, 8).map(t => ({
                    name: `#${t.tree_code}`,
                    Salud: t.avg_health_index
                  })) || []}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                  <XAxis type="number" domain={[0, 100]} stroke="#666" tick={{ fill: '#999' }} />
                  <YAxis dataKey="name" type="category" stroke="#666" tick={{ fill: '#999', fontSize: 11 }} width={60} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="Salud" fill={COLORS.healthy} radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </div>
      )}

      {/* Custom scrollbar styles */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1a1a1a;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #39ff14;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #2dd10f;
        }
      `}</style>
    </div>
  );
}
