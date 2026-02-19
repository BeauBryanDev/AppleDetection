import { useState, useEffect, useRef } from 'react';
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
    CheckCircle,
    Camera,
    Upload
} from 'lucide-react';
import { getMeRequest, updateUserRequest } from '../api/users';

export default function ProfilePage() {
    const { user, setUser } = useAuth();
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    const [profileData, setProfileData] = useState(null);
    const [avatarUrl, setAvatarUrl] = useState(null);
    const [uploadingAvatar, setUploadingAvatar] = useState(false);
    const fileInputRef = useRef(null);

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
            // Load avatar if exists
            if (res.data.avatar_url) {
                loadAvatarUrl(res.data.id);
            }
        } catch (err) {
            console.error('Error loading profile:', err);
            setError('Error al cargar el perfil');
        } finally {
            setLoading(false);
        }
    };

    const loadAvatarUrl = async (userId) => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`/api/v1/users/${userId}/profile-picture-url`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAvatarUrl(data.url);
            }
        } catch (err) {
            console.error('Error loading avatar URL:', err);
        }
    };

    const handleAvatarClick = () => {
        fileInputRef.current?.click();
    };

    const handleAvatarChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            setError('Image Format not allowed. Use JPG, PNG o WEBP.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setError('Image size cannot be larger than 5MB.');
            return;
        }

        try {
            setUploadingAvatar(true);
            setError(null);
            const token = localStorage.getItem('token');
            const formDataImg = new FormData();
            formDataImg.append('file', file);

            const res = await fetch(`/api/v1/users/${profileData.id}/profile-picture`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formDataImg
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Error while uploading image');
            }

            const updatedUser = await res.json();
            setProfileData(updatedUser);
            await loadAvatarUrl(updatedUser.id);
            setSuccess(true);
            setTimeout(() => setSuccess(false), 3000);
        } catch (err) {
            setError(err.message || 'Error while uploading image');
        } finally {
            setUploadingAvatar(false);
            e.target.value = '';
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

        if (formData.password && formData.password !== formData.confirmPassword) {
            setError('Password does not Match');
            return;
        }

        try {
            setSaving(true);
            setError(null);

            const updateData = {
                name: formData.name,
                phone_number: formData.phone_number || null
            };

            if (formData.password) {
                updateData.password = formData.password;
            }

            const res = await updateUserRequest(profileData.id, updateData);
            setProfileData(res.data);
            setUser(res.data);
            setSuccess(true);
            setEditing(false);
            setFormData({ ...formData, password: '', confirmPassword: '' });
            setTimeout(() => setSuccess(false), 3000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error : Update profile Error');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <div className="w-12 h-12 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin mb-4"></div>
                <p className="text-zinc-500 font-mono animate-pulse">Loading User Profile...</p>
            </div>
        );
    }

    if (!profileData) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <p className="text-zinc-500">Profile cannot be load</p>
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
                    <p className="text-zinc-500 text-sm font-mono">Edit my Account</p>
                </div>
                {!editing && (
                    <Button variant="primary" onClick={handleEdit}>
                        <Edit2 className="w-4 h-4" /> Edit Profile
                    </Button>
                )}
            </div>

            {/* Success Message */}
            {success && (
                <Card className="border-apple-green/30 bg-apple-green/10">
                    <div className="flex items-center gap-3 text-apple-green">
                        <CheckCircle className="w-5 h-5" />
                        <p className="font-medium">Profile has been Sucessfully Updated</p>
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
                        {/* Avatar Section */}
                        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-6 pb-6 border-b border-zinc-800">
                            <div className="relative group">
                                <div
                                    className="w-24 h-24 rounded-full border-2 border-zinc-700 group-hover:border-apple-green overflow-hidden bg-zinc-800 flex items-center justify-center cursor-pointer transition-all duration-300"
                                    onClick={handleAvatarClick}
                                >
                                    {uploadingAvatar ? (
                                        <div className="w-8 h-8 border-4 border-apple-green/30 border-t-apple-green rounded-full animate-spin"></div>
                                    ) : avatarUrl ? (
                                        <img
                                            src={avatarUrl}
                                            alt="Foto de perfil"
                                            className="w-full h-full object-cover"
                                            onError={() => setAvatarUrl(null)}
                                        />
                                    ) : (
                                        <User className="w-12 h-12 text-zinc-600" />
                                    )}
                                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-full">
                                        <Camera className="w-8 h-8 text-apple-green" />
                                    </div>
                                </div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/jpeg,image/png,image/jpg,image/webp"
                                    className="hidden"
                                    onChange={handleAvatarChange}
                                />
                            </div>
                            <div className="text-center sm:text-left">
                                <h3 className="text-white font-bold text-xl">{profileData.name}</h3>
                                <p className="text-zinc-500 text-sm font-mono">{profileData.email}</p>
                                <button
                                    onClick={handleAvatarClick}
                                    disabled={uploadingAvatar}
                                    className="mt-2 flex items-center gap-1 text-xs text-apple-green hover:text-apple-green/80 transition-colors disabled:opacity-50"
                                >
                                    <Upload className="w-3 h-3" />
                                    {uploadingAvatar ? 'Subiendo...' : 'Cambiar foto de perfil'}
                                </button>
                                <p className="text-xs text-zinc-600 mt-1">JPG, PNG o WEBP. Max 5MB.</p>
                            </div>
                        </div>

                        <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                            <User className="w-5 h-5 text-apple-green" />
                            Personal Information
                        </h3>

                        {editing ? (
                            <form onSubmit={handleSave} className="space-y-4">
                                <div>
                                    <Label htmlFor="name">Full Name</Label>
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

                                <div>
                                    <Label htmlFor="email">Email Address</Label>
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
                                    <p className="text-xs text-zinc-600 mt-1">Email Address Cannot be Changed, Request changes to administrator</p>
                                </div>

                                <div>
                                    <Label htmlFor="phone_number">Phone Number</Label>
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

                                <div className="pt-4 border-t border-zinc-800">
                                    <h4 className="text-white font-medium mb-3">Change Password(Opcional)</h4>
                                    <div className="space-y-3">
                                        <div>
                                            <Label htmlFor="password">New Password</Label>
                                            <Input
                                                id="password"
                                                type="password"
                                                value={formData.password}
                                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                                placeholder="Let it Empty"
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="confirmPassword">Confirm Password</Label>
                                            <Input
                                                id="confirmPassword"
                                                type="password"
                                                value={formData.confirmPassword}
                                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                                placeholder="Confirm New Password"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-2 pt-4">
                                    <Button type="submit" variant="primary" className="flex-1" isLoading={saving}>
                                        <Save className="w-4 h-4" />
                                        Save Changes
                                    </Button>
                                    <Button type="button" variant="ghost" onClick={handleCancel} disabled={saving}>
                                        Cancel
                                    </Button>
                                </div>
                            </form>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <User className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Name</p>
                                        <p className="text-white font-medium">{profileData.name}</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Mail className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Email</p>
                                        <p className="text-white font-medium">{profileData.email}</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Phone className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Phone Number</p>
                                        <p className="text-white font-medium">{profileData.phone_number || 'No especificado'}</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg">
                                    <Calendar className="w-5 h-5 text-zinc-500 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="text-xs text-zinc-500 font-mono uppercase">Joined From</p>
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
                    <Card className="border-zinc-800 bg-gradient-to-br from-zinc-900 to-black">
                        <div className="text-center">
                            <div className="flex justify-center mb-3">
                                <div className={`p-3 rounded-full border ${profileData.role === 'admin'
                                    ? 'bg-purple-500/10 border-purple-500/30'
                                    : 'bg-apple-green/10 border-apple-green/30'
                                    }`}>
                                    <Shield className={`w-6 h-6 ${profileData.role === 'admin' ? 'text-purple-500' : 'text-apple-green'}`} />
                                </div>
                            </div>
                            <p className="text-xs text-zinc-500 font-mono uppercase mb-1">Rol</p>
                            <h3 className={`text-xl font-bold ${profileData.role === 'admin' ? 'text-purple-500' : 'text-apple-green'}`}>
                                {profileData.role === 'admin' ? 'Administrador' :
                                    profileData.role === 'farmer' ? 'Agricultor' : 'Invitado'}
                            </h3>
                        </div>
                    </Card>

                    <Card className="border-zinc-800 bg-cyber-dark">
                        <div className="text-center">
                            <p className="text-xs text-zinc-500 font-mono uppercase mb-2">User ID</p>
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
