import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  History as HistoryIcon,
  Trash2,
  Search,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Image as ImageIcon
} from 'lucide-react';
import { getAllEstimatesRequest, deleteEstimateRequest } from '../api/history';

export default function HistoryPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 });

  useEffect(() => {
    loadHistory();
  }, [pagination.skip]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const res = await getAllEstimatesRequest(pagination.skip, pagination.limit);
      setRecords(res.data);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (recordId) => {
    if (!confirm('¿Estás seguro de eliminar este registro?')) return;
    try {
      await deleteEstimateRequest(recordId);
      loadHistory();
    } catch (err) {
      console.error('Error deleting record:', err);
      alert('Error al eliminar el registro');
    }
  };

  const filteredRecords = records.filter((record) =>
    record.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    record.id?.toString().includes(searchTerm)
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse">Cargando historial...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <HistoryIcon className="w-8 h-8 text-apple-green" />
            Historial de Estimaciones
          </h1>
          <p className="text-zinc-500 text-sm font-mono">
            Total de registros: {filteredRecords.length}
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Buscar por ID o nombre..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-600 focus:outline-none focus:border-apple-green/50"
          />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-zinc-800 bg-black/40">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                Total Procesadas
              </p>
              <h3 className="text-2xl font-bold text-white">{records.length}</h3>
            </div>
            <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-green">
              <ImageIcon className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card className="border-zinc-800 bg-black/40">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                Manzanas Sanas
              </p>
              <h3 className="text-2xl font-bold text-white">
                {records.reduce((sum, r) => sum + (r.healthy_count || 0), 0)}
              </h3>
            </div>
            <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-green">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card className="border-zinc-800 bg-black/40">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                Manzanas Dañadas
              </p>
              <h3 className="text-2xl font-bold text-white">
                {records.reduce((sum, r) => sum + (r.damaged_count || 0), 0)}
              </h3>
            </div>
            <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-red">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
        </Card>
      </div>

      {/* History Table */}
      <Card className="p-0 overflow-hidden border-zinc-800 bg-cyber-dark">
        <div className="p-4 border-b border-zinc-800 bg-black/20">
          <h3 className="font-bold text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-apple-green" />
            Registros Históricos
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-zinc-500 uppercase bg-black/40 font-mono">
              <tr>
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">Archivo</th>
                <th className="px-6 py-3 text-center">Sanas</th>
                <th className="px-6 py-3 text-center">Dañadas</th>
                <th className="px-6 py-3 text-center">Total</th>
                <th className="px-6 py-3 text-center">Índice Salud</th>
                <th className="px-6 py-3">Fecha</th>
                <th className="px-6 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredRecords.map((record) => (
                <tr key={record.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <span className="text-white font-mono">#{record.id}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-white font-medium truncate max-w-xs">
                      {record.filename || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-apple-green font-bold">{record.healthy_count || 0}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-apple-red font-bold">{record.damaged_count || 0}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-white font-bold">{record.total_count || 0}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${
                        record.health_index >= 80
                          ? 'bg-apple-green/10 text-apple-green'
                          : record.health_index >= 50
                          ? 'bg-yellow-500/10 text-yellow-500'
                          : 'bg-red-500/10 text-red-500'
                      }`}
                    >
                      {record.health_index?.toFixed(1) || 0}%
                    </span>
                  </td>
                  <td className="px-6 py-4 text-zinc-400 font-mono text-xs">
                    {record.created_at
                      ? new Date(record.created_at).toLocaleString()
                      : 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(record.id)}
                      className="hover:bg-apple-red/20 hover:text-apple-red"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))}
              {filteredRecords.length === 0 && (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-zinc-500">
                    {searchTerm
                      ? 'No se encontraron registros con ese criterio'
                      : 'No hay registros en el historial'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredRecords.length > 0 && (
          <div className="p-4 border-t border-zinc-800 bg-black/20 flex justify-between items-center">
            <p className="text-sm text-zinc-500 font-mono">
              Mostrando {Math.min(pagination.skip + 1, filteredRecords.length)} -{' '}
              {Math.min(pagination.skip + pagination.limit, filteredRecords.length)} de{' '}
              {filteredRecords.length}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.skip === 0}
                onClick={() =>
                  setPagination({ ...pagination, skip: Math.max(0, pagination.skip - pagination.limit) })
                }
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.skip + pagination.limit >= filteredRecords.length}
                onClick={() =>
                  setPagination({ ...pagination, skip: pagination.skip + pagination.limit })
                }
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
