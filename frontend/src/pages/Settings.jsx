import { useState, useEffect, useRef } from 'react';
import api from '../utils/api';
import { exportTradesToCSV, exportTradesToPDF } from '../utils/export';
import StrategyPicker from '../components/StrategyPicker';
import { useAuth } from '../hooks/useAuth';

export default function Settings() {
    const [activeTab, setActiveTab] = useState('profile');
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const { logout } = useAuth();

    const [allUsers, setAllUsers] = useState([]);
    const [userRole, setUserRole] = useState('user');

    const [profile, setProfile] = useState({ display_name: '' });
    const [passwords, setPasswords] = useState({ current_password: '', new_password: '' });
    const [avatarUploading, setAvatarUploading] = useState(false);

    const [preferences, setPreferences] = useState({
        theme: 'dark',
        default_strategy_ids: [],
            refresh_secs: 30
    });

    const [newInst, setNewInst] = useState({
        symbol: '', provider_symbol: '', market_code: 'FOREX',
        pip_size: '0.0001', contract_size: 100000, quote_ccy: 'USD'
    });

    const [downloading, setDownloading] = useState(false);
    const [restoring, setRestoring] = useState(false);
    const [restorePassword, setRestorePassword] = useState('');
    const [restoreFile, setRestoreFile] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [instRes, userRes, prefRes] = await Promise.all([
                    api.get('/instruments/'),
                                                                      api.get('/users/me'),
                                                                      api.get('/settings/preferences')
                ]);
                setInstruments(instRes.data);
                setProfile({ display_name: userRes.data.display_name || '' });
                setUserRole(userRes.data.role);

                if (userRes.data.role === 'admin') {
                    const allUsersRes = await api.get('/users/');
                    setAllUsers(allUsersRes.data);
                }

                setPreferences(prefRes.data);
            } catch (err) {
                console.error('Failed to load settings data', err);
            } finally {
                setLoading(false);
            }
        };
        fetchAll();
    }, []);

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        try {
            await api.put('/users/me', profile);
            alert('Profile updated');
        } catch (err) {
            alert(err.response?.data?.detail || 'Update failed');
        }
    };

    const handleUpdatePassword = async (e) => {
        e.preventDefault();
        try {
            await api.put('/users/me/password', passwords);
            alert('Password updated. Please log in again.');
            logout();
        } catch (err) {
            alert(err.response?.data?.detail || 'Password update failed');
        }
    };

    const handleAvatarUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setAvatarUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        try {
            await api.post('/users/me/avatar', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert('Avatar updated! Refresh the page to see changes.');
        } catch (err) {
            alert('Avatar upload failed');
        } finally {
            setAvatarUploading(false);
        }
    };

    const handleUpdatePreferences = async (e) => {
        e.preventDefault();
        try {
            await api.put('/settings/preferences', preferences);
            alert('Preferences saved');
        } catch (err) {
            alert('Failed to save preferences');
        }
    };

    const handleCreateInstrument = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...newInst, pip_size: parseFloat(newInst.pip_size), contract_size: parseInt(newInst.contract_size) };
            await api.post('/instruments/', payload);
            setNewInst({ symbol: '', provider_symbol: '', market_code: 'FOREX', pip_size: '0.0001', contract_size: 100000, quote_ccy: 'USD' });
            const res = await api.get('/instruments/');
            setInstruments(res.data);
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to add instrument');
        }
    };

    const handleDownloadBackup = async () => {
        setDownloading(true);
        try {
            const res = await api.get('/backup/download', { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `rj_backup_${new Date().getTime()}.zip`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert('Backup download failed.');
        } finally {
            setDownloading(false);
        }
    };

    const handleRestore = async (e) => {
        e.preventDefault();
        if (!restoreFile) return alert('Select a backup ZIP file first.');
        if (!window.confirm("WARNING: This will overwrite your current journal data. Proceed?")) return;

        setRestoring(true);
        const formData = new FormData();
        formData.append('file', restoreFile);
        formData.append('password', restorePassword);

        try {
            await api.post('/restore/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            alert('Restore complete! Logging you out to refresh state.');
            logout();
        } catch (err) {
            alert(err.response?.data?.detail || 'Restore failed.');
        } finally {
            setRestoring(false);
        }
    };

    // --- Admin Actions ---
    const handleToggleUserStatus = async (user) => {
        try {
            await api.put(`/users/${user.id}`, { is_active: !user.is_active, role: user.role });
            const res = await api.get('/users/');
            setAllUsers(res.data);
        } catch (err) {
            alert(err.response?.data?.detail || 'Status update failed');
        }
    };

    const handleChangeRole = async (user, newRole) => {
        try {
            await api.put(`/users/${user.id}`, { is_active: user.is_active, role: newRole });
            const res = await api.get('/users/');
            setAllUsers(res.data);
        } catch (err) {
            alert(err.response?.data?.detail || 'Role update failed');
        }
    };

    const handleDeleteUser = async (userId) => {
        const password = window.prompt("WARNING: This permanently deletes the user and ALL their trades, images, and data.\n\nEnter your admin password to confirm:");

        if (!password) {
            return; // Cancelled or empty
        }

        try {
            const formData = new FormData();
            formData.append('password', password);

            // Change from api.delete to api.delete with data (axios specific way to send body in DELETE)
            await api.delete(`/users/${userId}`, {
                data: formData,
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            // Refresh the user list after successful deletion
            const res = await api.get('/users/');
            setAllUsers(res.data);
            alert('User successfully deleted.');
        } catch (err) {
            alert(err.response?.data?.detail || 'Delete failed');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading Settings...</div>;

    const TabButton = ({ id, label, isDanger }) => (
        <button
        onClick={() => setActiveTab(id)}
        style={{
            background: 'none', border: 'none', padding: '0.5rem 1rem', fontSize: '1rem', cursor: 'pointer',
            color: activeTab === id ? (isDanger ? '#ef4444' : '#22d3ee') : '#94a3b8',
                                                    fontWeight: activeTab === id ? 'bold' : 'normal',
                                                    borderBottom: activeTab === id ? `2px solid ${isDanger ? '#ef4444' : '#22d3ee'}` : '2px solid transparent'
        }}
        >
        {label}
        </button>
    );

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #334155', marginBottom: '2rem', overflowX: 'auto' }}>
        <TabButton id="profile" label="Profile" />
        <TabButton id="preferences" label="Preferences" />
        <TabButton id="data" label="Instruments" />
        {userRole === 'admin' && <TabButton id="accounts" label="Accounts" />}
        <TabButton id="backup" label="Backup/Export" />
        <TabButton id="restore" label="Restore Data" isDanger={true} />
        </div>

        {activeTab === 'profile' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Profile Picture</h3>
            <label style={{ background: '#334155', color: '#f8fafc', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer', display: 'inline-block' }}>
            {avatarUploading ? 'Uploading...' : 'Upload New Avatar'}
            <input type="file" accept="image/*" onChange={handleAvatarUpload} disabled={avatarUploading} style={{ display: 'none' }} />
            </label>
            </div>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Personal Details</h3>
            <form onSubmit={handleUpdateProfile} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#94a3b8' }}>Display Name</label>
            <input value={profile.display_name} onChange={e => setProfile({...profile, display_name: e.target.value})} style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px' }}>Save Name</button>
            </form>
            </div>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Change Password</h3>
            <form onSubmit={handleUpdatePassword} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <input type="password" placeholder="Current Password" value={passwords.current_password} onChange={e => setPasswords({...passwords, current_password: e.target.value})} required style={{ padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            <input type="password" placeholder="New Password" value={passwords.new_password} onChange={e => setPasswords({...passwords, new_password: e.target.value})} required style={{ padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            <button type="submit" style={{ background: '#ef4444', color: '#f8fafc', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', width: 'fit-content' }}>Update Password</button>
            </form>
            </div>
            </div>
        )}

        {activeTab === 'preferences' && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Application Preferences</h3>
            <form onSubmit={handleUpdatePreferences} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <StrategyPicker selectedIds={preferences.default_strategy_ids || []} onChange={(val) => setPreferences({...preferences, default_strategy_ids: val})} />
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '-1rem 0 0 0' }}>These strategies will be pre-selected on your Performance Dashboard.</p>
            <div>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#94a3b8' }}>Live Price Refresh Interval (Seconds)</label>
            <input type="number" min="10" max="300" value={preferences.refresh_secs} onChange={e => setPreferences({...preferences, refresh_secs: parseInt(e.target.value)})} style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.75rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px' }}>Save Preferences</button>
            </form>
            </div>
        )}

        {activeTab === 'data' && (
            <>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Add Currency Pair</h3>
            <form onSubmit={handleCreateInstrument} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Display Symbol</label>
            <input value={newInst.symbol} onChange={e => setNewInst({...newInst, symbol: e.target.value.toUpperCase()})} placeholder="AUD/JPY" required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>API Symbol (yfinance/12Data)</label>
            <input value={newInst.provider_symbol} onChange={e => setNewInst({...newInst, provider_symbol: e.target.value.toUpperCase()})} placeholder="AUDJPY=X" required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Quote Currency</label>
            <input value={newInst.quote_ccy} onChange={e => setNewInst({...newInst, quote_ccy: e.target.value.toUpperCase()})} placeholder="JPY" required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Pip Size</label>
            <input type="number" step="any" value={newInst.pip_size} onChange={e => setNewInst({...newInst, pip_size: e.target.value})} placeholder="0.01" required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
            </div>
            </div>
            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.75rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', marginTop: '0.5rem' }}>+ Add Instrument</button>
            </form>
            </div>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Active Instruments</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '1rem' }}>
            {instruments.map(inst => (
                <div key={inst.id} style={{ background: '#0f172a', padding: '1rem', borderRadius: '4px', textAlign: 'center', border: '1px solid #334155' }}>
                <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>{inst.symbol}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Pip: {inst.pip_size}</div>
                </div>
            ))}
            </div>
            </div>
            </>
        )}

        {/* --- ADMIN ACCOUNTS TAB --- */}
        {activeTab === 'accounts' && userRole === 'admin' && (
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px' }}>
            <h3 style={{ marginTop: 0, color: '#f8fafc' }}>System Users</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#f8fafc' }}>
            <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
            <th style={{ padding: '1rem 0', color: '#94a3b8' }}>User</th>
            <th style={{ padding: '1rem 0', color: '#94a3b8' }}>Role</th>
            <th style={{ padding: '1rem 0', color: '#94a3b8' }}>Status</th>
            <th style={{ padding: '1rem 0', color: '#94a3b8', textAlign: 'right' }}>Actions</th>
            </tr>
            </thead>
            <tbody>
            {allUsers.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid #334155' }}>
                <td style={{ padding: '1rem 0' }}>{u.username} <br/><span style={{ fontSize: '0.75rem', color: '#94a3b8'}}>{u.email}</span></td>
                <td style={{ padding: '1rem 0' }}>
                <select
                value={u.role}
                onChange={(e) => handleChangeRole(u, e.target.value)}
                style={{ background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', padding: '0.3rem' }}
                >
                <option value="user">User</option>
                <option value="admin">Admin</option>
                </select>
                </td>
                <td style={{ padding: '1rem 0' }}>
                <button
                onClick={() => handleToggleUserStatus(u)}
                style={{ background: u.is_active ? '#22c55e20' : '#ef444420', color: u.is_active ? '#22c55e' : '#ef4444', border: 'none', padding: '0.3rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                {u.is_active ? 'Active' : 'Disabled'}
                </button>
                </td>
                <td style={{ padding: '1rem 0', textAlign: 'right' }}>
                <button
                onClick={() => handleDeleteUser(u.id)}
                style={{ background: 'transparent', color: '#ef4444', border: '1px solid #ef4444', padding: '0.3rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}
                >
                Delete
                </button>
                </td>
                </tr>
            ))}
            </tbody>
            </table>
            </div>
        )}

        {activeTab === 'backup' && (
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', borderLeft: '4px solid #3b82f6' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f8fafc' }}>Data Portability</h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.5', marginBottom: '2rem' }}>Download a full ZIP archive containing all JSON data and image attachments.</p>
            <button onClick={handleDownloadBackup} disabled={downloading} style={{ background: downloading ? '#334155' : '#3b82f6', color: '#f8fafc', padding: '1rem 2rem', fontWeight: 'bold', border: 'none', cursor: downloading ? 'not-allowed' : 'pointer', borderRadius: '4px', width: '100%', fontSize: '1.1rem' }}>
            {downloading ? 'Compiling Backup...' : '↓ Download Full Backup (.zip)'}
            </button>
            <h3 style={{ margin: '2rem 0 1rem 0', color: '#f8fafc' }}>Export Analytics</h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.5', marginBottom: '2rem' }}>Download a flat CSV file of all your trades for Excel/Google Sheets.</p>
            <button onClick={() => exportTradesToCSV()} style={{ background: '#10b981', color: '#f8fafc', padding: '1rem 2rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', width: '100%', fontSize: '1.1rem' }}>
            ↓ Export Trades to CSV
            </button>
            <button onClick={() => exportTradesToPDF()} style={{ background: '#ef4444', color: '#f8fafc', padding: '1rem 2rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', width: '100%', fontSize: '1.1rem', marginTop: '1rem' }}>
            ↓ Export Trades to PDF
            </button>
            </div>
        )}

        {activeTab === 'restore' && (
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#ef4444' }}>Restore System Data</h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.5', marginBottom: '2rem' }}>Uploading a backup ZIP will permanently overwrite your existing journal data. This cannot be undone.</p>
            <form onSubmit={handleRestore} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#f8fafc' }}>Select Backup File (.zip)</label>
            <input type="file" accept=".zip" ref={fileInputRef} onChange={e => setRestoreFile(e.target.files[0])} required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }} />
            </div>
            <div>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#f8fafc' }}>Confirm Password</label>
            <input type="password" value={restorePassword} onChange={e => setRestorePassword(e.target.value)} placeholder="Enter password to authorize..." required style={{ width: '100%', padding: '0.75rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }} />
            </div>
            <button type="submit" disabled={restoring} style={{ background: restoring ? '#334155' : '#ef4444', color: '#f8fafc', padding: '1rem', fontWeight: 'bold', border: 'none', cursor: restoring ? 'not-allowed' : 'pointer', borderRadius: '4px', marginTop: '0.5rem' }}>
            {restoring ? 'Restoring Data...' : 'Overwrite & Restore'}
            </button>
            </form>
            </div>
        )}
        </div>
    );
}
