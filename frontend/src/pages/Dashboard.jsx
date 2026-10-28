import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchPerformance = async () => {
            try {
                // Fetch performance stats (without strategy filter for now to get account-wide stats)
                const res = await api.get('/dashboard/performance');
                setStats(res.data);
            } catch (err) {
                setError('Failed to load performance statistics.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchPerformance();
    }, []);

    if (loading) return <div style={{ padding: '2rem' }}>Loading Dashboard...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    // Helper component for stat cards
    const StatCard = ({ title, value, prefix = '', suffix = '', isCurrency = false }) => {
        const isPositive = parseFloat(value) >= 0;
        const color = isCurrency ? (isPositive ? '#22c55e' : '#ef4444') : '#f8fafc';

        return (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', flex: 1 }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', color: '#94a3b8', textTransform: 'uppercase' }}>
            {title}
            </h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: color }}>
            {prefix}{value}{suffix}
            </div>
            </div>
        );
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, color: '#f8fafc' }}>Performance Dashboard</h2>
        </div>

        {/* High-Level Metrics */}
        {stats && (
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '3rem' }}>
            <StatCard
            title="Total Realized P&L"
            value={stats.total_pnl}
            prefix={stats.total_pnl > 0 ? '+' : ''}
            isCurrency={true}
            />
            <StatCard
            title="Win Rate"
            value={stats.win_rate}
            suffix="%"
            />
            <StatCard
            title="Profit Factor"
            value={stats.profit_factor}
            />
            <StatCard
            title="Expectancy"
            value={stats.expectancy}
            prefix="$"
            />
            <StatCard
            title="Total Closed Trades"
            value={stats.total_trades}
            />
            </div>
        )}

        {/* Equity Curve Placeholder */}
        <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', minHeight: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#94a3b8' }}>[Equity Curve Chart Will Go Here]</p>
        </div>
        </div>
    );
}
