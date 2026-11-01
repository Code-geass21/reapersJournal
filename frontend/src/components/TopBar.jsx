import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import ClockIST from './ClockIST';
import MiniPerformance from './MiniPerformance';
import api from '../utils/api';

export default function TopBar() {
    const { logout } = useAuth();
    const [alerts, setAlerts] = useState([]);
    const [isAlertsOpen, setIsAlertsOpen] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const fetchAlerts = async () => {
            try {
                if (!localStorage.getItem('token')) return;
                const res = await api.get('/alerts/');
                if (isMounted) setAlerts(res.data);
            } catch (err) {
                console.error("Failed to fetch alerts", err);
            }
        };

        fetchAlerts();
        const intervalId = setInterval(fetchAlerts, 30000); // Check every 30s
        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, []);

    const handleDismiss = async (alertId) => {
        try {
            await api.post(`/alerts/${alertId}/dismiss`);
            setAlerts(alerts.filter(a => a.id !== alertId));
        } catch (err) {
            console.error("Failed to dismiss alert", err);
        }
    };

    const handleConfirmClose = async (alertId) => {
        try {
            await api.post(`/alerts/${alertId}/confirm-close`);
            setAlerts(alerts.filter(a => a.id !== alertId));
            // In a real app, you might want to refresh global state or trigger a toast here
        } catch (err) {
            alert("Failed to confirm trade closure. It may already be closed.");
        }
    };

    const newAlertsCount = alerts.filter(a => a.status === 'new').length;

    return (
        <nav style={{
            background: '#1e293b',
            padding: '1rem 2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #334155'
        }}>

        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#22d3ee' }}>Reaper's Journal</h1>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
        <Link to="/" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Dashboard</Link>
        <Link to="/journal" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Journal</Link>
        <Link to="/strategies" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Strategies</Link>
        <Link to="/settings" style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 'bold' }}>Settings</Link>
        </div>
        </div>

        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <div style={{ paddingRight: '2rem', borderRight: '1px solid #334155' }}>
        <MiniPerformance />
        </div>

        {/* NEW: Alerts Widget */}
        <div style={{ position: 'relative' }}>
        <button
        onClick={() => setIsAlertsOpen(!isAlertsOpen)}
        style={{ background: 'transparent', border: 'none', cursor: 'pointer', position: 'relative', fontSize: '1.5rem' }}
        >
        🔔
        {newAlertsCount > 0 && (
            <span style={{
                position: 'absolute', top: 0, right: 0,
                background: '#ef4444', color: 'white',
                borderRadius: '50%', width: '16px', height: '16px',
                fontSize: '0.6rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold'
            }}>
            {newAlertsCount}
            </span>
        )}
        </button>

        {isAlertsOpen && (
            <div style={{
                position: 'absolute', top: '100%', right: 0, marginTop: '0.5rem',
                background: '#0f172a', border: '1px solid #334155', borderRadius: '8px',
                width: '320px', maxHeight: '400px', overflowY: 'auto', zIndex: 100,
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
            }}>
            <div style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ margin: 0, color: '#f8fafc' }}>Active Alerts</h4>
            <button onClick={() => setIsAlertsOpen(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>✕</button>
            </div>
            {alerts.length === 0 ? (
                <div style={{ padding: '1rem', color: '#94a3b8', textAlign: 'center' }}>No active alerts.</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                {alerts.map(alert => (
                    <div key={alert.id} style={{ padding: '1rem', borderBottom: '1px solid #334155' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: alert.kind === 'sl_hit' ? '#ef4444' : '#22c55e', textTransform: 'uppercase' }}>
                    {alert.kind.replace('_', ' ')}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                    </div>
                    <p style={{ margin: '0 0 1rem 0', fontSize: '0.875rem', color: '#f8fafc' }}>{alert.message}</p>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {(alert.kind === 'sl_hit' || alert.kind === 'tp_hit') && alert.trade_id && (
                        <button
                        onClick={() => handleConfirmClose(alert.id)}
                        style={{ flex: 1, background: '#eab308', color: '#0f172a', border: 'none', padding: '0.4rem', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.8rem' }}
                        >
                        Confirm Close
                        </button>
                    )}
                    <button
                    onClick={() => handleDismiss(alert.id)}
                    style={{ flex: 1, background: '#334155', color: '#f8fafc', border: 'none', padding: '0.4rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                    >
                    Dismiss
                    </button>
                    </div>
                    </div>
                ))}
                </div>
            )}
            </div>
        )}
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
