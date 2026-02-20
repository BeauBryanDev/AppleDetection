import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import {
  Trees,
  Plus,
  Edit2,
  Trash2,
  MapPin,
  Sprout,
  X,
  Save,
  AlertCircle
} from 'lucide-react';
import {
  getOrchardsRequest,
  createOrchardRequest,
  updateOrchardRequest,
  deleteOrchardRequest,
  getOrchardTreesRequest,
  createTreeRequest,
  updateTreeRequest,
  deleteTreeRequest
} from '../api/farming';

export default function FarmingPage() {
  const [orchards, setOrchards] = useState([]);
  const [selectedOrchard, setSelectedOrchard] = useState(null);
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [showOrchardModal, setShowOrchardModal] = useState(false);
  const [showTreeModal, setShowTreeModal] = useState(false);
  const [editingOrchard, setEditingOrchard] = useState(null);
  const [editingTree, setEditingTree] = useState(null);

  // Form states
  const [orchardForm, setOrchardForm] = useState({ name: '', location: '', n_trees: 0 });
  const [treeForm, setTreeForm] = useState({ tree_code: '', tree_type: '' });

  useEffect(() => {
    loadOrchards();
  }, []);

  useEffect(() => {
    if (selectedOrchard) {
      loadTrees(selectedOrchard.id);
    }
  }, [selectedOrchard]);

  const loadOrchards = async () => {
    try {
      setLoading(true);
      const res = await getOrchardsRequest();
      setOrchards(res.data);
      if (res.data.length > 0 && !selectedOrchard) {
        setSelectedOrchard(res.data[0]);
      }
    } catch (err) {
      console.error('Error loading orchards:', err);
      setError('Error al cargar los huertos');
    } finally {
      setLoading(false);
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

  const handleCreateOrchard = async (e) => {
    e.preventDefault();
    try {
      await createOrchardRequest(orchardForm);
      setShowOrchardModal(false);
      setOrchardForm({ name: '', location: '', n_trees: 0 });
      loadOrchards();
    } catch (err) {
      console.error('Error creating orchard:', err);
      alert('Error al crear el huerto');
    }
  };

  const handleUpdateOrchard = async (e) => {
    e.preventDefault();
    try {
      await updateOrchardRequest(editingOrchard.id, orchardForm);
      setShowOrchardModal(false);
      setEditingOrchard(null);
      setOrchardForm({ name: '', location: '', n_trees: 0 });
      loadOrchards();
    } catch (err) {
      console.error('Error updating orchard:', err);
      alert('Error al actualizar el huerto');
    }
  };

  const handleDeleteOrchard = async (orchardId) => {
    if (!confirm('¿Estás seguro? Se eliminarán todos los árboles e imágenes asociadas.')) return;
    try {
      await deleteOrchardRequest(orchardId);
      setSelectedOrchard(null);
      loadOrchards();
    } catch (err) {
      console.error('Error deleting orchard:', err);
      alert('Error al eliminar el huerto');
    }
  };

  const handleCreateTree = async (e) => {
    e.preventDefault();
    try {
      await createTreeRequest(selectedOrchard.id, treeForm);
      setShowTreeModal(false);
      setTreeForm({ tree_code: '', tree_type: '' });
      loadTrees(selectedOrchard.id);
    } catch (err) {
      console.error('Error creating tree:', err);
      alert('Error al crear el árbol');
    }
  };

  const handleUpdateTree = async (e) => {
    e.preventDefault();
    try {
      await updateTreeRequest(selectedOrchard.id, editingTree.id, treeForm);
      setShowTreeModal(false);
      setEditingTree(null);
      setTreeForm({ tree_code: '', tree_type: '' });
      loadTrees(selectedOrchard.id);
    } catch (err) {
      console.error('Error updating tree:', err);
      alert('Error al actualizar el árbol');
    }
  };

  const handleDeleteTree = async (treeId) => {
    if (!confirm('¿Estás seguro de eliminar este árbol?')) return;
    try {
      await deleteTreeRequest(selectedOrchard.id, treeId);
      loadTrees(selectedOrchard.id);
    } catch (err) {
      console.error('Error deleting tree:', err);
      alert('Error al eliminar el árbol');
    }
  };

  const openCreateOrchardModal = () => {
    setEditingOrchard(null);
    setOrchardForm({ name: '', location: '', n_trees: 0 });
    setShowOrchardModal(true);
  };

  const openEditOrchardModal = (orchard) => {
    setEditingOrchard(orchard);
    setOrchardForm({ name: orchard.name, location: orchard.location, n_trees: orchard.n_trees });
    setShowOrchardModal(true);
  };

  const openCreateTreeModal = () => {
    setEditingTree(null);
    setTreeForm({ tree_code: '', tree_type: '' });
    setShowTreeModal(true);
  };

  const openEditTreeModal = (tree) => {
    setEditingTree(tree);
    setTreeForm({ tree_code: tree.tree_code, tree_type: tree.tree_type });
    setShowTreeModal(true);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse">Cargando datos...</p>
      </div>
    );
  }

  return (
    <div className="space-y-5 sm:space-y-6 lg:space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 flex items-center gap-2 sm:gap-3">
            <Trees className="w-6 h-6 sm:w-8 sm:h-8 text-apple-green" />
            Gestión de Huertos
          </h1>
          <p className="text-zinc-500 text-sm font-mono">Administra tus huertos y árboles</p>
        </div>
        <Button variant="primary" onClick={openCreateOrchardModal}>
          <Plus className="w-4 h-4" /> Nuevo Huerto
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-apple-red/10 border border-apple-red/20 rounded-lg text-apple-red flex items-center gap-2">
          <AlertCircle className="w-5 h-5" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6 lg:gap-8">
        {/* Orchards List */}
        <div className="lg:col-span-1">
          <Card className="p-4 border-zinc-800 bg-cyber-dark">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-apple-green" />
              Mis Huertos ({orchards.length})
            </h3>
            <div className="space-y-2">
              {orchards.map((orchard) => (
                <div
                  key={orchard.id}
                  onClick={() => setSelectedOrchard(orchard)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedOrchard?.id === orchard.id
                      ? 'bg-apple-green/20 border border-apple-green/50'
                      : 'bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-white font-medium">{orchard.name}</h4>
                      <p className="text-xs text-zinc-500">{orchard.location}</p>
                      <p className="text-xs text-zinc-600 mt-1">
                        {orchard.n_trees} árboles registrados
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openEditOrchardModal(orchard);
                        }}
                        className="p-1 hover:bg-zinc-800 rounded"
                      >
                        <Edit2 className="w-3 h-3 text-zinc-500" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteOrchard(orchard.id);
                        }}
                        className="p-1 hover:bg-apple-red/20 rounded"
                      >
                        <Trash2 className="w-3 h-3 text-apple-red" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {orchards.length === 0 && (
                <p className="text-center text-zinc-600 py-8 text-sm">
                  No hay huertos registrados
                </p>
              )}
            </div>
          </Card>
        </div>

        {/* Trees List */}
        <div className="lg:col-span-2">
          {selectedOrchard ? (
            <Card className="p-4 border-zinc-800 bg-cyber-dark">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 mb-4">
                <h3 className="text-white font-bold flex items-center gap-2 break-words">
                  <Sprout className="w-4 h-4 text-apple-green" />
                  Árboles de {selectedOrchard.name} ({trees.length})
                </h3>
                <Button variant="outline" size="sm" onClick={openCreateTreeModal}>
                  <Plus className="w-4 h-4" /> Agregar Árbol
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {trees.map((tree) => (
                  <div
                    key={tree.id}
                    className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="text-white font-medium">#{tree.tree_code}</h4>
                        <p className="text-xs text-zinc-500">{tree.tree_type || 'Sin tipo'}</p>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => openEditTreeModal(tree)}
                          className="p-1.5 hover:bg-zinc-800 rounded"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-zinc-500" />
                        </button>
                        <button
                          onClick={() => handleDeleteTree(tree.id)}
                          className="p-1.5 hover:bg-apple-red/20 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-apple-red" />
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-zinc-600 font-mono">
                      ID: {tree.id} | Huerto: {selectedOrchard.name}
                    </div>
                  </div>
                ))}
                {trees.length === 0 && (
                  <div className="col-span-2 text-center text-zinc-600 py-12">
                    No hay árboles registrados en este huerto
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card className="p-12 border-zinc-800 bg-cyber-dark text-center">
              <Trees className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">Selecciona un huerto para ver sus árboles</p>
            </Card>
          )}
        </div>
      </div>

      {/* Orchard Modal */}
      {showOrchardModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md border-apple-green/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {editingOrchard ? 'Editar Huerto' : 'Nuevo Huerto'}
              </h3>
              <button
                onClick={() => setShowOrchardModal(false)}
                className="p-2 hover:bg-zinc-800 rounded"
              >
                <X className="w-5 h-5 text-zinc-400" />
              </button>
            </div>

            <form onSubmit={editingOrchard ? handleUpdateOrchard : handleCreateOrchard} className="space-y-4">
              {!editingOrchard && (
                <>
                  <div>
                    <Label>Nombre del Huerto</Label>
                    <Input
                      value={orchardForm.name}
                      onChange={(e) => setOrchardForm({ ...orchardForm, name: e.target.value })}
                      placeholder="Ej: Huerto Norte"
                      required
                    />
                  </div>

                  <div>
                    <Label>Ubicación</Label>
                    <Input
                      value={orchardForm.location}
                      onChange={(e) => setOrchardForm({ ...orchardForm, location: e.target.value })}
                      placeholder="Ej: Sector A, Parcela 12"
                      required
                    />
                  </div>
                </>
              )}

              <div>
                <Label>Número de Árboles</Label>
                <Input
                  type="number"
                  value={orchardForm.n_trees}
                  onChange={(e) => setOrchardForm({ ...orchardForm, n_trees: parseInt(e.target.value) || 0 })}
                  placeholder="0"
                  required
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="primary" className="flex-1">
                  <Save className="w-4 h-4" />
                  {editingOrchard ? 'Actualizar' : 'Crear'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowOrchardModal(false)}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Tree Modal */}
      {showTreeModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md border-apple-green/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {editingTree ? 'Editar Árbol' : 'Nuevo Árbol'}
              </h3>
              <button
                onClick={() => setShowTreeModal(false)}
                className="p-2 hover:bg-zinc-800 rounded"
              >
                <X className="w-5 h-5 text-zinc-400" />
              </button>
            </div>

            <form onSubmit={editingTree ? handleUpdateTree : handleCreateTree} className="space-y-4">
              <div>
                <Label>Código del Árbol</Label>
                <Input
                  value={treeForm.tree_code}
                  onChange={(e) => setTreeForm({ ...treeForm, tree_code: e.target.value })}
                  placeholder="Ej: A-001"
                  required
                />
              </div>

              <div>
                <Label>Tipo/Variedad</Label>
                <Input
                  value={treeForm.tree_type}
                  onChange={(e) => setTreeForm({ ...treeForm, tree_type: e.target.value })}
                  placeholder="Ej: Granny Smith"
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="primary" className="flex-1">
                  <Save className="w-4 h-4" />
                  {editingTree ? 'Actualizar' : 'Crear'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowTreeModal(false)}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
