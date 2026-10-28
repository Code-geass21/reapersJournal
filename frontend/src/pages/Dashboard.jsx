import { useState, useEffect } from 'react';
import api from '../utils/api';
// Import Recharts components
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchPerformance = async () => {
            try {
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

    // Custom Tooltip for the Recharts graph
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const val = payload[0].value;
            return (
                <div style={{ background: '#0f172a', padding: '1rem', border: '1px solid #334155', borderRadius: '4px' }}>
                <p style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>{label}</p>
                <p style={{ color: val >= 0 ? '#22c55e' : '#ef4444', margin: 0, fontWeight: 'bold' }}>
                P&L: {val > 0 ? '+' : ''}{val}
                </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, color: '#f8fafc' }}>Performance Dashboard</h2>
        </div>

        {stats && (
            <>
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

            {/* Recharts Equity Curve */}
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', minHeight: '400px' }}>
            <h3 style={{ margin: '0 0 2rem 0', color: '#f8fafc' }}>Cumulative Equity Curve</h3>

            {stats.equity_curve && stats.equity_curve.length > 0 ? (
                <div style={{ width: '100%', height: 350 }}>
                <ResponsiveContainer>
                <LineChart data={stats.equity_curve} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
                tickFormatter={(tick) => tick.split(' ')[0]} // Show only date, not time
                />
                <YAxis
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                type="monotone"
                dataKey="cumulative_pnl"
                stroke="#22d3ee"
                strokeWidth={3}
                dot={{ r: 4, fill: '#22d3ee', strokeWidth: 0 }}
                activeDot={{ r: 6, fill: '#f8fafc' }}
                />
                </LineChart>
                </ResponsiveContainer>
                </div>
            ) : (
                <p style={{ color: '#94a3b8', textAlign: 'center', marginTop: '4rem' }}>
                Not enough closed trades to generate an equity curve.
                </p>
            )}
            </div>
            </>
        )}
        </div>
    );
}
