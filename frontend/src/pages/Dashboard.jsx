import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Trees, Sprout, Activity, AlertTriangle, MapPin, Calendar, CheckCircle2, Search, PieChart as PieChartIcon } from 'lucide-react';
import { getOrchardsRequest } from '../api/farming';
import { getDashboardAnalyticsRequest } from '../api/analytics';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

// Cyberpunk colors
const COLORS = {
  healthy: '#39ff14',
  damaged: '#ff073a',
  total: '#00d4ff'
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [orchard, setOrchard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        // 1. Obtener huertos
        const orchardsRes = await getOrchardsRequest();
        const orchardsData = orchardsRes.data;

        if (!orchardsData || orchardsData.length === 0) {
          setError("No se encontraron huertos asociados a tu cuenta.");
          setLoading(false);
          return;
        }

        // Usamos el primer huerto de la lista por defecto
        const currentOrchard = orchardsData[0];
        setOrchard(currentOrchard);

        // 2. Obtener analíticas usando el ID del huerto
        const analyticsRes = await getDashboardAnalyticsRequest(currentOrchard.id);
        setAnalytics(analyticsRes.data);

      } catch (err) {
        console.error("Error cargando dashboard:", err);
        setError("Error de conexión con el servidor de análisis.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // --- MAPEO DE DATOS (Backend JSON -> Frontend UI) ---
  const summary = analytics?.summary;
  const detections = analytics?.recent_detections || [];

  // Calculate totals for pie chart
  const totalHealthyApples = detections.reduce((sum, d) => sum + d.healthy_apples, 0);
  const totalDamagedApples = detections.reduce((sum, d) => sum + d.damaged_apples, 0);

  const appleDistribution = [
    { name: 'Sanas', value: totalHealthyApples, color: COLORS.healthy },
    { name: 'Dañadas', value: totalDamagedApples, color: COLORS.damaged }
  ];

  // Custom tooltip
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

  // Progress bar component
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
    { 
      title: "Árboles Totales", 
      // Si el objeto 'orchard' tiene n_trees, lo usamos. Si no, mostramos un placeholder.
      value: orchard?.n_trees || "N/A", 
      icon: Trees, 
      color: "text-blue-400" 
    },
    { 
      title: "Manzanas Detectadas", 
      value: summary.total_apples_found, // Viene directo de tu JSON
      icon: Sprout, 
      color: "text-apple-green" 
    },
    { 
      title: "Salud Promedio", 
      value: `${summary.health_score_avg}%`, // Viene directo de tu JSON (ej: 74.01)
      icon: Activity, 
      color: summary.health_score_avg > 75 ? "text-apple-green" : "text-yellow-400" 
    },
    { 
      title: "Imágenes Procesadas", 
      value: summary.images_processed, // Viene directo de tu JSON
      icon: Search, 
      color: "text-purple-400" 
    },
  ] : [];

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse">Sincronizando datos del huerto...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* 1. Encabezado del Huerto */}
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            {orchard?.name}
          </h1>
          <div className="flex items-center gap-4 text-sm text-zinc-400 font-mono">
            <span className="flex items-center gap-1">
               <MapPin className="w-4 h-4 text-apple-green" /> {orchard?.location}
            </span>
            <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-700 text-xs">
               ID: {orchard?.id}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" /> {error}
        </div>
      )}

      {/* 2. Tarjetas de Estadísticas (KPIs) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <Card key={i} className="border-zinc-800/60 bg-black/40 hover:bg-zinc-900/40 transition-colors">
            <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">{stat.title}</p>
                  <h3 className="text-2xl font-bold text-white">{stat.value}</h3>
                </div>
                <div className={`p-2 rounded-lg bg-zinc-900/50 ${stat.color}`}>
                  <stat.icon className="w-5 h-5" />
                </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 3. Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Apple Distribution Pie Chart */}
        <div>
          <Card className="p-6 border-zinc-800 bg-gradient-to-br from-zinc-900/90 to-black mb-6">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-apple-green" />
              Distribución de Manzanas
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={appleDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                >
                  {appleDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-2 mt-4">
              <div className="text-center p-2 bg-apple-green/10 rounded-lg border border-apple-green/30">
                <p className="text-xs text-zinc-400">Sanas</p>
                <p className="text-xl font-bold text-apple-green">{totalHealthyApples}</p>
              </div>
              <div className="text-center p-2 bg-apple-red/10 rounded-lg border border-apple-red/30">
                <p className="text-xs text-zinc-400">Dañadas</p>
                <p className="text-xl font-bold text-apple-red">{totalDamagedApples}</p>
              </div>
            </div>
          </Card>

          {/* Health Score with Progress */}
          <Card className="bg-gradient-to-br from-zinc-900 to-black border-zinc-800 p-6">
            <div className="mb-2 text-zinc-500 text-xs font-mono uppercase tracking-widest">Calidad Global</div>
            <div className="text-5xl font-bold text-white mb-4">
              {summary?.health_score_avg.toFixed(0)}%
            </div>
            <ProgressBar
              value={summary?.health_score_avg || 0}
              max={100}
              color={summary?.health_score_avg >= 75 ? 'bg-apple-green' : 'bg-yellow-500'}
            />
            <div className="text-sm text-apple-green flex items-center justify-center gap-1 mt-4">
              <CheckCircle2 className="w-4 h-4" /> {summary?.health_score_avg >= 75 ? 'Huerto Saludable' : 'Requiere Atención'}
            </div>
          </Card>
        </div>

        {/* Recent Activity Table */}
        <div className="lg:col-span-2">
            <Card className="p-0 overflow-hidden border-zinc-800 bg-cyber-dark">
                <div className="p-4 border-b border-zinc-800 bg-black/20 flex justify-between items-center">
                    <h3 className="font-bold text-white flex items-center gap-2">
                        <Activity className="w-4 h-4 text-apple-green" /> Actividad Reciente
                    </h3>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-zinc-500 uppercase bg-black/40 font-mono">
                            <tr>
                                <th className="px-6 py-3">Fecha / ID</th>
                                <th className="px-6 py-3">Árbol</th>
                                <th className="px-6 py-3 text-center">Salud</th>
                                <th className="px-6 py-3 text-right">Manzanas</th>
                                <th className="px-6 py-3 text-center">Estado</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800/50">
                            {detections.map((item) => (
                                <tr key={item.prediction_id} className="hover:bg-zinc-800/30 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="text-white font-medium">#{item.prediction_id}</div>
                                        <div className="text-[10px] text-zinc-600 font-mono">
                                            {new Date(item.timestamp).toLocaleString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-zinc-300">
                                        Tree-{item.tree_id}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                                            item.health_index >= 80 ? 'bg-apple-green/10 text-apple-green' : 
                                            item.health_index >= 50 ? 'bg-yellow-500/10 text-yellow-500' : 'bg-red-500/10 text-red-500'
                                        }`}>
                                            {item.health_index.toFixed(0)}%
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono text-zinc-400">
                                        <span className="text-white font-bold">{item.total_apples}</span> Total
                                        <div className="text-[10px] text-red-400">
                                            {item.damaged_apples} dañadas
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        {item.damaged_apples === 0 ? (
                                            <CheckCircle2 className="w-5 h-5 text-apple-green mx-auto" />
                                        ) : (
                                            <AlertTriangle className="w-5 h-5 text-yellow-500 mx-auto" />
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {detections.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="px-6 py-8 text-center text-zinc-500">
                                        No hay actividad reciente registrada.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>

      </div>
    </div>
  );
}