import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Label } from '../components/ui/Label';
import {
  Upload,
  Image as ImageIcon,
  Sprout,
  AlertTriangle,
  CheckCircle2,
  Activity,
  FileImage,
  X,
  Zap
} from 'lucide-react';
import { uploadImageEstimateRequest } from '../api/estimator';
import { getOrchardsRequest, getOrchardTreesRequest } from '../api/farming';

export default function EstimatorPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Orchard & Tree selection
  const [orchards, setOrchards] = useState([]);
  const [trees, setTrees] = useState([]);
  const [selectedOrchard, setSelectedOrchard] = useState('');
  const [selectedTree, setSelectedTree] = useState('');

  useEffect(() => {
    loadOrchards();
  }, []);

  useEffect(() => {
    if (selectedOrchard) {
      loadTrees(selectedOrchard);
    } else {
      setTrees([]);
      setSelectedTree('');
    }
  }, [selectedOrchard]);

  const loadOrchards = async () => {
    try {
      const res = await getOrchardsRequest();
      setOrchards(res.data);
    } catch (err) {
      console.error('Error loading orchards:', err);
    }
  };

  const loadTrees = async (orchardId) => {
    try {
      const res = await getOrchardTreesRequest(orchardId);
      setTrees(res.data);
    } catch (err) {
      console.error('Error loading trees:', err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Por favor selecciona un archivo de imagen válido');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        setError('El archivo no debe superar 10MB');
        return;
      }

      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setResult(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Por favor selecciona una imagen');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      const orchardId = selectedOrchard ? parseInt(selectedOrchard) : null;
      const treeId = selectedTree ? parseInt(selectedTree) : null;

      const res = await uploadImageEstimateRequest(formData, orchardId, treeId);
      setResult(res.data);
    } catch (err) {
      console.error('Error processing image:', err);
      setError(err.response?.data?.detail || 'Error al procesar la imagen');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setSelectedOrchard('');
    setSelectedTree('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Zap className="w-8 h-8 text-apple-green" />
            Estimador de Rendimiento
          </h1>
          <p className="text-zinc-500 text-sm font-mono">
            Carga una imagen para detectar manzanas automáticamente
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="space-y-4">
          <Card className="border-zinc-800 bg-cyber-dark">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-apple-green" />
              Subir Imagen
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* File Input */}
              <div>
                <Label htmlFor="file-upload">Seleccionar Imagen</Label>
                <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-zinc-800 border-dashed rounded-lg hover:border-zinc-700 transition-colors">
                  <div className="space-y-1 text-center">
                    {previewUrl ? (
                      <div className="relative">
                        <img
                          src={previewUrl}
                          alt="Preview"
                          className="mx-auto h-48 w-auto rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={handleReset}
                          className="absolute top-2 right-2 p-2 bg-black/70 rounded-full hover:bg-black"
                        >
                          <X className="w-4 h-4 text-white" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <FileImage className="mx-auto h-12 w-12 text-zinc-600" />
                        <div className="flex text-sm text-zinc-400">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer rounded-md font-medium text-apple-green hover:text-apple-green-dim"
                          >
                            <span>Subir archivo</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              accept="image/*"
                              className="sr-only"
                              onChange={handleFileChange}
                            />
                          </label>
                          <p className="pl-1">o arrastra y suelta</p>
                        </div>
                        <p className="text-xs text-zinc-600">PNG, JPG hasta 10MB</p>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Orchard Selection */}
              <div>
                <Label htmlFor="orchard">Huerto (Opcional)</Label>
                <select
                  id="orchard"
                  value={selectedOrchard}
                  onChange={(e) => setSelectedOrchard(e.target.value)}
                  className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:border-apple-green/50"
                >
                  <option value="">Sin asignar (Modo Invitado)</option>
                  {orchards.map((orchard) => (
                    <option key={orchard.id} value={orchard.id}>
                      {orchard.name} - {orchard.location}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tree Selection */}
              {selectedOrchard && trees.length > 0 && (
                <div>
                  <Label htmlFor="tree">Árbol (Opcional)</Label>
                  <select
                    id="tree"
                    value={selectedTree}
                    onChange={(e) => setSelectedTree(e.target.value)}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:border-apple-green/50"
                  >
                    <option value="">Sin especificar</option>
                    {trees.map((tree) => (
                      <option key={tree.id} value={tree.id}>
                        {tree.tree_code} {tree.tree_type ? `- ${tree.tree_type}` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-apple-red/10 border border-apple-red/20 rounded-lg text-apple-red flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex gap-2">
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  isLoading={loading}
                  disabled={!selectedFile || loading}
                >
                  <Zap className="w-4 h-4" />
                  {loading ? 'Analizando...' : 'Procesar Imagen'}
                </Button>
                {(selectedFile || result) && (
                  <Button type="button" variant="ghost" onClick={handleReset}>
                    Limpiar
                  </Button>
                )}
              </div>
            </form>
          </Card>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {result ? (
            <>
              <Card className="border-apple-green/30 bg-gradient-to-br from-zinc-900 to-black">
                <div className="text-center">
                  <p className="text-xs text-zinc-500 font-mono uppercase mb-2">
                    Resultado del Análisis
                  </p>
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <CheckCircle2 className="w-8 h-8 text-apple-green" />
                    <h2 className="text-4xl font-bold text-white">
                      {result.total_count || 0}
                    </h2>
                  </div>
                  <p className="text-zinc-400">Manzanas Detectadas</p>
                </div>
              </Card>

              <div className="grid grid-cols-2 gap-4">
                <Card className="border-zinc-800 bg-black/40">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                        Sanas
                      </p>
                      <h3 className="text-2xl font-bold text-apple-green">
                        {result.healthy_count || 0}
                      </h3>
                    </div>
                    <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-green">
                      <Sprout className="w-5 h-5" />
                    </div>
                  </div>
                </Card>

                <Card className="border-zinc-800 bg-black/40">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                        Dañadas
                      </p>
                      <h3 className="text-2xl font-bold text-apple-red">
                        {result.damaged_count || 0}
                      </h3>
                    </div>
                    <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-red">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                  </div>
                </Card>
              </div>

              <Card className="border-zinc-800 bg-cyber-dark">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-bold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-apple-green" />
                    Índice de Salud
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-bold ${
                      (result.health_index || 0) >= 80
                        ? 'bg-apple-green/10 text-apple-green'
                        : (result.health_index || 0) >= 50
                        ? 'bg-yellow-500/10 text-yellow-500'
                        : 'bg-red-500/10 text-red-500'
                    }`}
                  >
                    {(result.health_index || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-zinc-900 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      (result.health_index || 0) >= 80
                        ? 'bg-apple-green'
                        : (result.health_index || 0) >= 50
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${result.health_index || 0}%` }}
                  />
                </div>
              </Card>

              <Card className="border-zinc-800 bg-cyber-dark">
                <h3 className="text-white font-bold mb-3 flex items-center gap-2">
                  <FileImage className="w-5 h-5 text-apple-green" />
                  Detalles
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Archivo:</span>
                    <span className="text-white font-mono">{result.filename || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">ID Predicción:</span>
                    <span className="text-white font-mono">#{result.id || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Timestamp:</span>
                    <span className="text-white font-mono text-xs">
                      {result.created_at
                        ? new Date(result.created_at).toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </Card>
            </>
          ) : (
            <Card className="border-zinc-800 bg-cyber-dark p-12 text-center">
              <ImageIcon className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500 mb-2">Sin resultados</p>
              <p className="text-sm text-zinc-600">
                Sube y procesa una imagen para ver los resultados aquí
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
