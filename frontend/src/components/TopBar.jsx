import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import ClockIST from './ClockIST';
import MiniPerformance from './MiniPerformance';

export default function TopBar() {
    const { logout } = useAuth();

    return (
        <nav style={{
            background: '#1e293b',
            padding: '1rem 2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #334155'
        }}>

        {/* Left Side: Branding & Navigation */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#22d3ee' }}>Reaper's Journal</h1>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
        <Link to="/" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Dashboard</Link>
        <Link to="/journal" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Journal</Link>
        <Link to="/strategies" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Strategies</Link>
        <Link to="/settings" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Settings</Link>
        </div>
        </div>

        {/* Right Side: Mini Stats, Clock, and Logout */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <div style={{ paddingRight: '2rem', borderRight: '1px solid #334155' }}>
        <MiniPerformance />
        </div>
        <ClockIST />
        <button
        onClick={logout}
        style={{
            background: 'transparent',
            color: '#ef4444',
            border: '1px solid #ef4444',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            borderRadius: '4px',
            fontWeight: 'bold'
        }}
        >
        Logout
        </button>
        </div>
        </nav>
    );
}
