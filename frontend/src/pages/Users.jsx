import { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import {
  Users as UsersIcon,
  Plus,
  Edit2,
  Trash2,
  Shield,
  User,
  Mail,
  Phone,
  X,
  Save,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { getMeRequest, createUserRequest, updateUserRequest, deleteUserRequest, getUsersRequest } from '../api/users';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [error, setError] = useState(null);

  // Form state
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    phone_number: '',
    password: '',
    role: 'farmer'
  });

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      setLoading(true);
      const res = await getMeRequest();
      setCurrentUser(res.data);

      // Solo los admin pueden ver esta página
      if (res.data.role !== 'admin') {
        setError('No tienes permisos para acceder a esta página');
      } else {
        await loadUsers();
      }
    } catch (err) {
      console.error('Error loading current user:', err);
      setError('Error al cargar datos del usuario');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const res = await getUsersRequest();
      console.log('Users loaded:', res.data);
      setUsers(res.data);
      setError(null);
    } catch (err) {
      console.error('Error loading users:', err);
      setError('Error al cargar la lista de usuarios: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await createUserRequest(userForm);
      setShowModal(false);
      setUserForm({ name: '', email: '', phone_number: '', password: '', role: 'farmer' });
      alert('Usuario creado exitosamente');
      loadUsers();
    } catch (err) {
      console.error('Error creating user:', err);
      alert('Error al crear usuario');
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        name: userForm.name,
        phone_number: userForm.phone_number
      };
      if (userForm.password) {
        updateData.password = userForm.password;
      }

      await updateUserRequest(editingUser.id, updateData);
      setShowModal(false);
      setEditingUser(null);
      setUserForm({ name: '', email: '', phone_number: '', password: '', role: 'farmer' });
      alert('Usuario actualizado exitosamente');
      loadUsers();
    } catch (err) {
      console.error('Error updating user:', err);
      alert('Error al actualizar usuario');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return;
    try {
      await deleteUserRequest(userId);
      alert('Usuario eliminado exitosamente');
      loadUsers();
    } catch (err) {
      console.error('Error deleting user:', err);
      alert('Error al eliminar usuario');
    }
  };

  const openCreateModal = () => {
    setEditingUser(null);
    setUserForm({ name: '', email: '', phone_number: '', password: '', role: 'farmer' });
    setShowModal(true);
  };

  const openEditModal = (user) => {
    setEditingUser(user);
    setUserForm({
      name: user.name,
      email: user.email,
      phone_number: user.phone_number || '',
      password: '',
      role: user.role
    });
    setShowModal(true);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-500 font-mono animate-pulse">Cargando usuarios...</p>
      </div>
    );
  }

  if (error && currentUser?.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Shield className="w-16 h-16 text-apple-red mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Acceso Denegado</h2>
        <p className="text-zinc-500">Solo los administradores pueden acceder a esta página</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Shield className="w-8 h-8 text-apple-green" />
            Gestión de Usuarios
          </h1>
          <p className="text-zinc-500 text-sm font-mono">Panel de administración</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={loadUsers}
            disabled={loadingUsers}
          >
            <RefreshCw className={`w-4 h-4 ${loadingUsers ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button variant="primary" onClick={openCreateModal}>
            <Plus className="w-4 h-4" /> Crear Usuario
          </Button>
        </div>
      </div>

      {/* Current User Info */}
      <Card className="border-apple-green/30 bg-gradient-to-br from-zinc-900 to-black">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-apple-green/10 rounded-full border border-apple-green/30">
            <User className="w-6 h-6 text-apple-green" />
          </div>
          <div>
            <p className="text-xs text-zinc-500 font-mono uppercase">Usuario Actual</p>
            <h3 className="text-white font-bold">{currentUser?.name}</h3>
            <p className="text-sm text-zinc-400">{currentUser?.email}</p>
          </div>
          <div className="ml-auto">
            <span className="px-3 py-1 rounded-full bg-apple-green/10 text-apple-green text-xs font-bold border border-apple-green/30">
              {currentUser?.role}
            </span>
          </div>
        </div>
      </Card>

      {/* Users List */}
      <Card className="p-4 border-zinc-800 bg-cyber-dark">
        <h3 className="text-white font-bold mb-4 flex items-center gap-2">
          <UsersIcon className="w-5 h-5 text-apple-green" />
          Lista de Usuarios ({users.length})
        </h3>

        {error && currentUser?.role === 'admin' && (
          <div className="mb-4 p-3 bg-apple-red/10 border border-apple-red/30 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-apple-red flex-shrink-0" />
            <p className="text-apple-red text-sm">{error}</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-zinc-400">
            <thead className="text-xs text-zinc-500 uppercase bg-zinc-900/50">
              <tr>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Contacto</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loadingUsers ? (
                <tr>
                  <td colSpan="4" className="text-center py-8">
                    <div className="flex items-center justify-center gap-2 text-zinc-500">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Cargando usuarios...</span>
                    </div>
                  </td>
                </tr>
              ) : (
                <>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-zinc-800 hover:bg-zinc-800/30">
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">{user.name}</div>
                        <div className="text-xs text-zinc-500">{user.email}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${user.role === 'admin' ? 'bg-purple-500/10 text-purple-500 border-purple-500/30' :
                          user.role === 'farmer' ? 'bg-apple-green/10 text-apple-green border-apple-green/30' :
                            'bg-zinc-700/30 text-zinc-400 border-zinc-600'
                          }`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {user.phone_number || '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <button onClick={() => openEditModal(user)} className="p-1 hover:text-apple-green transition-colors">
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDeleteUser(user.id)} className="p-1 hover:text-apple-red transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan="4" className="text-center py-8 text-zinc-500">
                        No hay usuarios registrados
                      </td>
                    </tr>
                  )}
                </>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md border-apple-green/30 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {editingUser ? 'Editar Usuario' : 'Crear Usuario'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-zinc-800 rounded"
              >
                <X className="w-5 h-5 text-zinc-400" />
              </button>
            </div>

            <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser} className="space-y-4">
              <div>
                <Label htmlFor="name">Nombre Completo</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    id="name"
                    value={userForm.name}
                    onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                    className="pl-10"
                    placeholder="Juan Pérez"
                    required
                  />
                </div>
              </div>

              {!editingUser && (
                <div>
                  <Label htmlFor="email">Correo Electrónico</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      id="email"
                      type="email"
                      value={userForm.email}
                      onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                      className="pl-10"
                      placeholder="usuario@agro.com"
                      required
                    />
                  </div>
                </div>
              )}

              <div>
                <Label htmlFor="phone">Teléfono (Opcional)</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    id="phone"
                    type="tel"
                    value={userForm.phone_number}
                    onChange={(e) => setUserForm({ ...userForm, phone_number: e.target.value })}
                    className="pl-10"
                    placeholder="+57 300 123 4567"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="password">
                  {editingUser ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña'}
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  placeholder="••••••••"
                  required={!editingUser}
                />
              </div>

              {!editingUser && (
                <div>
                  <Label htmlFor="role">Rol</Label>
                  <select
                    id="role"
                    value={userForm.role}
                    onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:border-apple-green/50"
                  >
                    <option value="farmer">FARMER (Agricultor)</option>
                    <option value="admin">ADMIN (Administrador)</option>
                    <option value="guest">GUEST (Invitado)</option>
                  </select>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button type="submit" variant="primary" className="flex-1">
                  <Save className="w-4 h-4" />
                  {editingUser ? 'Actualizar' : 'Crear Usuario'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowModal(false)}
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
