import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import api from '../utils/api';

export default function Sidebar() {
    const { theme, toggleTheme } = useTheme();
    const [profile, setProfile] = useState(null);
    const [avatarUrl, setAvatarUrl] = useState(null);

    // Fetch user profile and avatar on mount
    useEffect(() => {
        const loadProfile = async () => {
            try {
                if (!localStorage.getItem('token')) return;
                const res = await api.get('/users/me');
                setProfile(res.data);

                if (res.data.avatar_attachment_id) {
                    const avatarRes = await api.get(`/attachments/${res.data.avatar_attachment_id}/file`, { responseType: 'blob' });
                    setAvatarUrl(URL.createObjectURL(avatarRes.data));
                }
            } catch (err) {
                console.error("Failed to load profile", err);
            }
        };
        loadProfile();
    }, []);

    const linkStyle = ({ isActive }) => ({
        display: 'block',
        padding: '0.75rem 1rem',
        color: isActive ? '#22d3ee' : '#cbd5e1',
        textDecoration: 'none',
        fontWeight: isActive ? 'bold' : 'normal',
        background: isActive ? '#334155' : 'transparent',
        borderRadius: '4px',
        marginBottom: '0.5rem',
        transition: 'background 0.2s, color 0.2s'
    });

    return (
        <aside style={{
            width: '250px',
            background: '#1e293b',
            padding: '2rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            borderRight: '1px solid #334155',
            height: '100vh',
            boxSizing: 'border-box'
        }}>
        {/* Header with dynamic Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem', padding: '0 0.5rem' }}>
        {avatarUrl ? (
            <img src={avatarUrl} alt="Avatar" style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }} />
        ) : (
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f8fafc', fontWeight: 'bold' }}>
            {profile?.display_name?.charAt(0) || profile?.username?.charAt(0) || 'U'}
            </div>
        )}
        <h2 style={{ color: '#22d3ee', margin: 0, fontSize: '1.25rem' }}>
        Reaper's Journal
        </h2>
        </div>

        <nav style={{ flex: 1 }}>
        <NavLink to="/" style={linkStyle}>Dashboard</NavLink>
        <NavLink to="/journal" style={linkStyle}>Journal</NavLink>
        <NavLink to="/strategies" style={linkStyle}>Strategies</NavLink>
        <NavLink to="/logs" style={linkStyle}>Logs</NavLink>
        <NavLink to="/settings" style={linkStyle}>Settings</NavLink>
        <NavLink to="/help" style={linkStyle}>Help</NavLink>
        </nav>

        <div style={{
            marginTop: 'auto',
            borderTop: '1px solid #334155',
            paddingTop: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
        }}>
        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Theme</span>
        <button
        onClick={toggleTheme}
        style={{
            background: '#334155',
            border: 'none',
            color: '#f8fafc',
            padding: '0.25rem 0.5rem',
            borderRadius: '4px',
            cursor: 'pointer'
        }}
        >
        {theme === 'dark' ? '🌙' : '☀️'}
        </button>
        </div>
        </aside>
    );
}
