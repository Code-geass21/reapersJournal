import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function MiniPerformance() {
    const [stats, setStats] = useState(null);

    useEffect(() => {
        let isMounted = true;

        const fetchStats = async () => {
            try {
                // Fetch the same endpoint the main dashboard uses
                const res = await api.get('/dashboard/performance');
                if (isMounted) setStats(res.data);
            } catch (err) {
                console.error("Failed to load mini performance", err);
            }
        };

        // Fetch on load, and update every 60 seconds so the mini-strip stays fresh
        fetchStats();
        const intervalId = setInterval(fetchStats, 60000);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, []);

    if (!stats) return <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Loading Stats...</div>;

    const isPositive = stats.total_pnl >= 0;

    return (
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', fontSize: '0.875rem' }}>
        <div>
        <span style={{ color: '#94a3b8', marginRight: '0.5rem' }}>Total P&L:</span>
        <span style={{ fontWeight: 'bold', color: isPositive ? '#22c55e' : '#ef4444' }}>
        {isPositive ? '+' : ''}{stats.total_pnl}
        </span>
        </div>
        <div>
        <span style={{ color: '#94a3b8', marginRight: '0.5rem' }}>Win Rate:</span>
        <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{stats.win_rate}%</span>
        </div>
        <div>
        <span style={{ color: '#94a3b8', marginRight: '0.5rem' }}>Trades:</span>
        <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{stats.total_trades}</span>
        </div>
        </div>
    );
}
