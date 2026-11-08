
import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import api from '../utils/api';

export default function Sidebar() {
    const { theme, toggleTheme } = useTheme();
    const [profile, setProfile] = useState(null);
    const [avatarUrl, setAvatarUrl] = useState(null);

    // FIX FOR BUG 27: Extract loading logic into a reusable function
    const loadProfile = async () => {
        try {
            if (!localStorage.getItem('token')) return;

            const res = await api.get('/users/me');
            setProfile(res.data);

            if (res.data.avatar_attachment_id) {
                // Ensure we don't cache the old image by appending a timestamp query
                const timestamp = new Date().getTime();

                const avatarRes = await api.get(
                    `/attachments/${res.data.avatar_attachment_id}/file?t=${timestamp}`,
                    { responseType: 'blob' }
                );

                // Cleanup old object URL to prevent memory leaks
                if (avatarUrl) {
                    URL.revokeObjectURL(avatarUrl);
                }

                setAvatarUrl(URL.createObjectURL(avatarRes.data));
            }
        } catch (err) {
            console.error("Failed to load profile", err);
        }
    };

    useEffect(() => {
        loadProfile();

        // Listen for a custom event emitted by the Settings page
        const handleAvatarUpdate = () => {
            loadProfile();
        };

        window.addEventListener('avatar-updated', handleAvatarUpdate);

        return () => {
            window.removeEventListener('avatar-updated', handleAvatarUpdate);

            // Final cleanup of the blob URL
            if (avatarUrl) URL.revokeObjectURL(avatarUrl);
        };
    }, []);

    // Keep linkStyle exactly as it is
    const linkStyle = ({ isActive }) => ({
        display: 'block',
        padding: '0.75rem 1rem',
        color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
        textDecoration: 'none',
        fontWeight: isActive ? 'bold' : 'normal',
        background: isActive ? 'var(--border-color)' : 'transparent',
        borderRadius: '4px',
        marginBottom: '0.5rem',
        transition: 'background 0.2s, color 0.2s'
    });

    return (
        <aside style={{
            width: '250px',
            background: 'var(--bg-panel)',
            padding: '2rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            borderRight: '1px solid var(--border-color)',
            height: '100vh',
            boxSizing: 'border-box'
        }}>
        {/* Header with dynamic Avatar */}
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '2rem',
            padding: '0 0.5rem'
        }}>
        {avatarUrl ? (
            <img
            src={avatarUrl}
            alt="Avatar"
            style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                objectFit: 'cover'
            }}
            />
        ) : (
            <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-primary)',
                fontWeight: 'bold'
            }}>
            {profile?.display_name?.charAt(0) ||
                profile?.username?.charAt(0) || 'U'}
                </div>
        )}

        <h2 style={{
            color: 'var(--accent)',
            margin: 0,
            fontSize: '1.25rem'
        }}>
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
            borderTop: '1px solid var(--border-color)',
            paddingTop: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
        }}>
        <span style={{
            color: 'var(--text-muted)',
            fontSize: '0.875rem'
        }}>
        Theme
        </span>

        <button
        onClick={toggleTheme}
        style={{
            background: 'var(--border-color)',
            border: 'none',
            color: 'var(--text-primary)',
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
