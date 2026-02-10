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
  ChevronDown
} from 'lucide-react';
import {
  getUserSummaryRequest,
  getTreesSummaryRequest,
  getHealthTrendRequest
} from '../api/analytics';
import { getOrchardsRequest } from '../api/farming';

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
        getHealthTrendRequest(orchardId, 10)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-apple-green" />
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

      {/* Orchards Summary Table */}
      <div>
        <h2 className="text-white font-bold mb-4 flex items-center gap-2">
          <Trees className="w-5 h-5 text-apple-green" />
          Resumen por Huerto
        </h2>
        <Card className="p-0 overflow-hidden border-zinc-800 bg-cyber-dark">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-zinc-500 uppercase bg-black/40 font-mono">
                <tr>
                  <th className="px-6 py-3">Huerto</th>
                  <th className="px-6 py-3">Ubicación</th>
                  <th className="px-6 py-3 text-center">Árboles</th>
                  <th className="px-6 py-3 text-center">Imágenes</th>
                  <th className="px-6 py-3 text-center">Manzanas</th>
                  <th className="px-6 py-3 text-center">Salud Promedio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {userSummary?.orchards?.map((orchard) => (
                  <tr key={orchard.orchard_id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-white font-medium">{orchard.orchard_name}</div>
                    </td>
                    <td className="px-6 py-4 text-zinc-400">{orchard.location}</td>
                    <td className="px-6 py-4 text-center text-white font-mono">{orchard.n_trees}</td>
                    <td className="px-6 py-4 text-center text-white font-mono">{orchard.images_processed}</td>
                    <td className="px-6 py-4 text-center text-white font-mono">{orchard.apples_detected}</td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          orchard.avg_health >= 80
                            ? 'bg-apple-green/10 text-apple-green'
                            : orchard.avg_health >= 50
                            ? 'bg-yellow-500/10 text-yellow-500'
                            : 'bg-red-500/10 text-red-500'
                        }`}
                      >
                        {orchard.avg_health.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
                {(!userSummary?.orchards || userSummary.orchards.length === 0) && (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center text-zinc-500">
                      No hay huertos registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Orchard Details Section */}
      {selectedOrchard && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trees Summary */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white font-bold flex items-center gap-2">
                <Sprout className="w-5 h-5 text-apple-green" />
                Análisis por Árbol
              </h2>
              {/* Orchard Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowOrchardDropdown(!showOrchardDropdown)}
                  className="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white text-sm flex items-center gap-2 hover:bg-zinc-800"
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
                        className="w-full px-4 py-2 text-left text-white hover:bg-zinc-800 text-sm transition-colors"
                      >
                        {orchard.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <Card className="p-4 border-zinc-800 bg-cyber-dark max-h-[400px] overflow-y-auto">
              <div className="space-y-2">
                {treesSummary?.trees?.map((tree) => (
                  <div
                    key={tree.tree_id}
                    className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="text-white font-medium">#{tree.tree_code}</h4>
                        <p className="text-xs text-zinc-500">{tree.tree_type || 'Sin tipo'}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          tree.avg_health_index >= 80
                            ? 'bg-apple-green/10 text-apple-green'
                            : tree.avg_health_index >= 50
                            ? 'bg-yellow-500/10 text-yellow-500'
                            : 'bg-red-500/10 text-red-500'
                        }`}
                      >
                        {tree.avg_health_index.toFixed(1)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-zinc-400">
                      <div>Imágenes: <span className="text-white">{tree.total_images}</span></div>
                      <div>Manzanas: <span className="text-white">{tree.total_apples_detected}</span></div>
                    </div>
                  </div>
                ))}
                {(!treesSummary?.trees || treesSummary.trees.length === 0) && (
                  <p className="text-center text-zinc-600 py-8">No hay datos de árboles</p>
                )}
              </div>
            </Card>
          </div>

          {/* Health Trend */}
          <div>
            <h2 className="text-white font-bold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-apple-green" />
              Tendencia de Salud
            </h2>
            <Card className="p-4 border-zinc-800 bg-cyber-dark">
              <div className="space-y-3">
                {healthTrend?.trend?.map((point, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <span className="text-xs text-zinc-600 font-mono w-32 flex-shrink-0">
                      {new Date(point.timestamp).toLocaleDateString()}
                    </span>
                    <div className="flex-1 bg-zinc-900 rounded-full h-6 relative overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          point.health_index >= 80
                            ? 'bg-apple-green'
                            : point.health_index >= 50
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${point.health_index}%` }}
                      />
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
                        {point.health_index.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
                {(!healthTrend?.trend || healthTrend.trend.length === 0) && (
                  <p className="text-center text-zinc-600 py-8">No hay datos de tendencia</p>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
