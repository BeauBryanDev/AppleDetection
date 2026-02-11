import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import {
    User,
    Mail,
    Phone,
    Calendar,
    Edit2,
    Save,
    X,
    Shield,
    CheckCircle
} from 'lucide-react';
import { getMeRequest, updateUserRequest } from '../api/users';

export default function ProfilePage() {
    const { user, setUser } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    const [profileData, setProfileData] = useState(null);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        phone_number: '',
        password: '',
        confirmPassword: ''
    });

    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            setLoading(true);
            const res = await getMeRequest();
            setProfileData(res.data);
            setFormData({
                name: res.data.name,
                phone_number: res.data.phone_number || '',
                password: '',
                confirmPassword: ''
            });
        } catch (err) {
            console.error('Error loading profile:', err);
            setError('Error al cargar el perfil');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = () => {
        setEditing(true);
        setError(null);
        setSuccess(false);
    };

    const handleCancel = () => {
        setEditing(false);
        setFormData({
            name: profileData.name,
            phone_number: profileData.phone_number || '',
            password: '',
            confirmPassword: ''
        });
        setError(null);
    };

    const handleSave = async (e) => {
        e.preventDefault();

        // Validate passwords match if changing password
        if (formData.password && formData.password !== formData.confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }

        try {
            setSaving(true);
            setError(null);

            const updateData = {
                name: formData.name,
                phone_number: formData.phone_number || null
            };

            // Only include password if it's being changed
            if (formData.password) {
                updateData.password = formData.password;
            }

            const res = await updateUserRequest(profileData.id, updateData);

            // Update local profile data
            setProfileData(res.data);

            // Update auth context
            setUser(res.data);

            setSuccess(true);
            setEditing(false);

            // Clear password fields
            setFormData({
                ...formData,
                password: '',
                confirmPassword: ''
            });

            // Hide success message after 3 seconds
            setTimeout(() => setSuccess(false), 3000);
        } catch (err) {
            console.error('Error updating profile:', err);
            setError(err.response?.data?.detail || 'Error al actualizar el perfil');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
                <p className="text-zinc-500 font-mono animate-pulse">Cargando perfil...</p>
            </div>
        );
    }

    if (!profileData) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <p className="text-zinc-500">No se pudo cargar el perfil</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        <User className="w-8 h-8 text-apple-green" />
                        Mi Perfil
                    </h1>
                    <p className="text-zinc-500 text-sm font-mono">Configuración de cuenta</p>
                </div>
                {!editing && (
                    <Button variant="primary" onClick={handleEdit}>
                        <Edit2 className="w-4 h-4" /> Editar Perfil
                    </Button>
                )}
            </div>

            {/* Success Message */}
            {success && (
                <Card className="border-apple-green/30 bg-apple-green/10">
                    <div className="flex items-center gap-3 text-apple-green">
                        <CheckCircle className="w-5 h-5" />
                        <p className="font-medium">Perfil actualizado exitosamente</p>
                    </div>
                </Card>
            )}

            {/* Error Message */}
            {error && (
                <Card className="border-apple-red/30 bg-apple-red/10">
                    <div className="flex items-center gap-3 text-apple-red">
                        <X className="w-5 h-5" />
                        <p className="font-medium">{error}</p>
                    </div>
                </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Profile Info Card */}
                <div className="lg:col-span-2">
                    <Card className="border-zinc-800 bg-cyber-dark">
                        <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                            <User className="w-5 h-5 text-apple-green" />
                            Información Personal
                        </h3>

                        {editing ? (
                            <form onSubmit={handleSave} className="space-y-4">
                                {/* Name */}
                                <div>
                                    <Label htmlFor="name">Nombre Completo</Label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                                        <Input
                                            id="name"
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="pl-10"
                                            required
                                        />
                                    </div>
                                </div>

                                {/* Email (Read-only) */}
                                <div>
                                    <Label htmlFor="email">Correo Electrónico</Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                                        <Input
                                            id="email"
                                            type="email"
                                            value={profileData.email}
                                            className="pl-10 bg-zinc-900/50 cursor-not-allowed"
                                            disabled
                                        />
                                    </div>
                                    <p className="text-xs text-zinc-600 mt-1">El correo no se puede cambiar</p>
                                </div>

                                {/* Phone */}
                                <div>
                                    <Label htmlFor="phone_number">Teléfono (Opcional)</Label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                                        <Input
                                            id="phone_number"
                                            type="tel"
                                            value={formData.phone_number}
                                            onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                                            className="pl-10"
                                            placeholder="+57 300 123 4567"
                                        />
                                    </div>
                                </div>

                                {/* Password */}
                                <div className="pt-4 border-t border-zinc-800">
                                    <h4 className="text-white font-medium mb-3">Cambiar Contraseña (Opcional)</h4>

                                    <div className="space-y-3">
                                        <div>
                                            <Label htmlFor="password">Nueva Contraseña</Label>
                                            <Input
                                                id="password"
                                                type="password"
                                                value={formData.password}
                                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                                placeholder="Dejar vacío para no cambiar"
                                            />
                                        </div>

                                        <div>
                                            <Label htmlFor="confirmPassword">Confirmar Contraseña</Label>
                                            <Input
                                                id="confirmPassword"
                                                type="password"
                                                value={formData.confirmPassword}
                                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                                placeholder="Confirmar nueva contraseña"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-2 pt-4">
                                    <Button type="submit" variant="primary" className="flex-1" isLoading={saving}>
                                        <Save className="w-4 h-4" />
                                        Guardar Cambios
                                    </Button>
                                    <Button type="button" variant="ghost" onClick={handleCancel} disabled={saving}>
                                        Cancelar
                                    </Button>
                                </div>
                            </form>
                        ) : (
                            <div className="space-y-4">
                                {/* Name Display */}
                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <User className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Nombre</p>
                                        <p className="text-white font-medium">{profileData.name}</p>
                                    </div>
                                </div>

                                {/* Email Display */}
                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Mail className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Email</p>
                                        <p className="text-white font-medium">{profileData.email}</p>
                                    </div>
                                </div>

                                {/* Phone Display */}
                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Phone className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Teléfono</p>
                                        <p className="text-white font-medium">{profileData.phone_number || 'No especificado'}</p>
                                    </div>
                                </div>

                                {/* Created Date */}
                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Calendar className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Miembro Desde</p>
                                        <p className="text-white font-medium">
                                            {new Date(profileData.created_at).toLocaleDateString('es-ES', {
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric'
                                            })}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </Card>
                </div>

                {/* Role & Stats Card */}
                <div className="space-y-6">
                    {/* Role Card */}
                    <Card className="border-zinc-800 bg-gradient-to-br from-zinc-900 to-black">
                        <div className="text-center">
                            <div className="flex justify-center mb-3">
                                <div className={`p-3 rounded-full border ${profileData.role === 'admin'
                                        ? 'bg-purple-500/10 border-purple-500/30'
                                        : 'bg-apple-green/10 border-apple-green/30'
                                    }`}>
                                    <Shield className={`w-6 h-6 ${profileData.role === 'admin' ? 'text-purple-500' : 'text-apple-green'
                                        }`} />
                                </div>
                            </div>
                            <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Rol</p>
                            <h3 className={`text-xl font-bold ${profileData.role === 'admin' ? 'text-purple-500' : 'text-apple-green'
                                }`}>
                                {profileData.role === 'admin' ? 'Administrador' :
                                    profileData.role === 'farmer' ? 'Agricultor' : 'Invitado'}
                            </h3>
                        </div>
                    </Card>

                    {/* User ID Card */}
                    <Card className="border-zinc-800 bg-cyber-dark">
                        <div className="text-center">
                            <p className="text-xs text-zinc-500 font-mono uppercase mb-2">ID de Usuario</p>
                            <p className="text-2xl font-bold font-mono text-apple-green">
                                #{String(profileData.id).padStart(4, '0')}
                            </p>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
}
