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
  Image as ImageIcon,
  X,
  ZoomIn
} from 'lucide-react';
import { getAllEstimatesRequest, deleteEstimateRequest } from '../api/history';

export default function HistoryPage() {
  const [records, setRecords] = useState([]);
  const [imageUrls, setImageUrls] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 });
  const [selectedImage, setSelectedImage] = useState(null);

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

  const getImageUrl = async (recordId) => {
    if (imageUrls[recordId]) return imageUrls[recordId];
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/v1/history/${recordId}/image-url`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setImageUrls(prev => ({ ...prev, [recordId]: data.url }));
      return data.url;
    } catch {
      return null;
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
    <div className="space-y-5 sm:space-y-6 lg:space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 flex items-center gap-2 sm:gap-3">
            <HistoryIcon className="w-6 h-6 sm:w-8 sm:h-8 text-apple-green" />
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
                <th className="px-4 sm:px-6 py-3">ID</th>
                <th className="px-4 sm:px-6 py-3">Imagen</th>
                <th className="px-4 sm:px-6 py-3">Archivo</th>
                <th className="px-4 sm:px-6 py-3 text-center">Sanas</th>
                <th className="px-4 sm:px-6 py-3 text-center">Dañadas</th>
                <th className="px-4 sm:px-6 py-3 text-center">Total</th>
                <th className="px-4 sm:px-6 py-3 text-center">Índice Salud</th>
                <th className="px-4 sm:px-6 py-3">Fecha</th>
                <th className="px-4 sm:px-6 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredRecords.map((record) => (
                <tr key={record.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 sm:px-6 py-4">
                    <span className="text-white font-mono">#{record.id}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4">
                    {record.filename ? (
                      <div className="relative group">
                        <img
                          src={imageUrls[record.id] || ''}
                          alt={record.filename}
                          className="w-16 h-16 object-cover rounded-lg border-2 border-zinc-700 hover:border-apple-green cursor-pointer transition-all hover:shadow-lg hover:shadow-apple-green/20 hover:scale-105"
                          onClick={() => {
                            setSelectedImage(record);
                            getImageUrl(record.id);
                          }}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="64" height="64"%3E%3Crect fill="%23333" width="64" height="64"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23666"%3E?%3C/text%3E%3C/svg%3E';
                          }}
                          ref={(el) => {
                            if (el && !imageUrls[record.id]) {
                              getImageUrl(record.id);
                            }
                          }}
                        />
                        <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg pointer-events-none">
                          <ZoomIn className="w-6 h-6 text-apple-green drop-shadow-lg" />
                        </div>
                      </div>
                    ) : (
                      <div className="w-16 h-16 bg-zinc-800 rounded-lg flex items-center justify-center">
                        <ImageIcon className="w-6 h-6 text-zinc-600" />
                      </div>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4">
                    <div className="text-white font-medium truncate max-w-[180px] sm:max-w-xs text-sm">
                      {record.filename || 'N/A'}
                    </div>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center">
                    <span className="text-apple-green font-bold">{record.healthy_count || 0}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center">
                    <span className="text-apple-red font-bold">{record.damaged_count || 0}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center">
                    <span className="text-white font-bold">{record.total_count || 0}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center">
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
                  <td className="px-4 sm:px-6 py-4 text-zinc-400 font-mono text-xs">
                    {record.created_at
                      ? new Date(record.created_at).toLocaleString()
                      : 'N/A'}
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center">
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
                  <td colSpan="9" className="px-6 py-12 text-center text-zinc-500">
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
          <div className="p-4 border-t border-zinc-800 bg-black/20 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
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

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-6xl w-full max-h-[90vh] animate-in zoom-in-95 duration-200">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-12 right-0 p-2 text-white hover:text-apple-green transition-colors rounded-full hover:bg-zinc-800/50"
            >
              <X className="w-8 h-8" />
            </button>

            <div className="absolute -top-12 left-0 text-white font-mono text-sm space-y-1">
              <p className="text-zinc-400">Registro #{selectedImage.id}</p>
              <p className="text-zinc-500 text-xs">{selectedImage.filename}</p>
            </div>

            <div className="bg-black rounded-lg overflow-hidden border-2 border-apple-green/30 shadow-2xl shadow-apple-green/10">
              <img
                src={imageUrls[selectedImage.id] || ''}
                alt={selectedImage.filename}
                className="w-full h-auto max-h-[85vh] object-contain"
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4" onClick={(e) => e.stopPropagation()}>
              <Card className="bg-black/60 border-zinc-800 backdrop-blur-sm">
                <div className="text-center">
                  <p className="text-xs text-zinc-500 mb-1">Sanas</p>
                  <p className="text-2xl font-bold text-apple-green">{selectedImage.healthy_count || 0}</p>
                </div>
              </Card>
              <Card className="bg-black/60 border-zinc-800 backdrop-blur-sm">
                <div className="text-center">
                  <p className="text-xs text-zinc-500 mb-1">Dañadas</p>
                  <p className="text-2xl font-bold text-apple-red">{selectedImage.damaged_count || 0}</p>
                </div>
              </Card>
              <Card className="bg-black/60 border-zinc-800 backdrop-blur-sm">
                <div className="text-center">
                  <p className="text-xs text-zinc-500 mb-1">Total</p>
                  <p className="text-2xl font-bold text-white">{selectedImage.total_count || 0}</p>
                </div>
              </Card>
              <Card className="bg-black/60 border-zinc-800 backdrop-blur-sm">
                <div className="text-center">
                  <p className="text-xs text-zinc-500 mb-1">Índice Salud</p>
                  <p className={`text-2xl font-bold ${
                    selectedImage.health_index >= 80 ? 'text-apple-green' :
                    selectedImage.health_index >= 50 ? 'text-yellow-500' : 'text-red-500'
                  }`}>
                    {selectedImage.health_index?.toFixed(1) || 0}%
                  </p>
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
