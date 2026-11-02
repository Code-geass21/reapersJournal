import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

export default function Sidebar() {
    const { theme, toggleTheme } = useTheme();

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
        <h2 style={{ color: '#22d3ee', margin: '0 0 2rem 1rem', fontSize: '1.25rem' }}>
        Reaper's Journal
        </h2>

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
