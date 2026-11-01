import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import api from '../utils/api';

export default function Sidebar() {
    const location = useLocation();
    const { theme, toggleTheme } = useTheme();
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                if (!localStorage.getItem('token')) return;
                const res = await api.get('/users/me');
                setUser(res.data);
            } catch (err) {
                console.error('Failed to fetch user', err);
            }
        };
        fetchUser();
    }, []);

    const navItems = [
        { path: '/', label: 'Dashboard', icon: '📊' },
        { path: '/journal', label: 'Journal', icon: '📓' },
        { path: '/strategies', label: 'Strategies', icon: '♟️' },
        { path: '/logs', label: 'Logs', icon: '📋' },
        { path: '/settings', label: 'Settings', icon: '⚙️' },
        { path: '/help', label: 'Help', icon: '❓' },
    ];

    return (
        <aside style={{
            width: '250px',
            background: '#1e293b',
            borderRight: '1px solid #334155',
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            position: 'sticky',
            top: 0
        }}>
        <div style={{ padding: '1.5rem 1.5rem 1rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#22d3ee' }}>Reaper's Journal</h1>
        </div>

        <nav style={{ flex: 1, padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {navItems.map(item => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
                <Link
                key={item.path}
                to={item.path}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    color: isActive ? '#22d3ee' : '#94a3b8',
                    background: isActive ? '#33415550' : 'transparent',
                    fontWeight: isActive ? 'bold' : 'normal',
                    transition: 'all 0.2s'
                }}
                >
                <span>{item.icon}</span>
                {item.label}
                </Link>
            );
        })}
        </nav>

        <div style={{ padding: '1.5rem', borderTop: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
            width: '40px', height: '40px', borderRadius: '50%', background: '#334155',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f8fafc', fontWeight: 'bold'
        }}>
        {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ color: '#f8fafc', fontWeight: 'bold', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
        {user?.display_name || user?.username || 'Trader'}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'capitalize' }}>
        {user?.role || 'User'}
        </div>
        </div>
        </div>

        <button
        onClick={toggleTheme}
        style={{
            background: 'transparent', border: '1px solid #334155', color: '#cbd5e1',
            padding: '0.5rem', borderRadius: '4px', cursor: 'pointer', display: 'flex', justifyContent: 'center', gap: '0.5rem', alignItems: 'center'
        }}
        >
        {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>
        </div>
        </aside>
    );
}
