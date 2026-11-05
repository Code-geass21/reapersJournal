import { useState, useEffect } from 'react';
import api from '../utils/api';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    BarChart, Bar, Cell
} from 'recharts';
import NewsPanel from '../components/NewsPanel';
import StrategyPicker from '../components/StrategyPicker';

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [loadingStats, setLoadingStats] = useState(true);
    const [error, setError] = useState('');

    const [selectedStrats, setSelectedStrats] = useState([]);
    const [isReady, setIsReady] = useState(false);

    // 1. Fetch user preferences once to get default strategies
    useEffect(() => {
        api.get('/settings/preferences')
        .then(res => {
            const defaults = res.data.default_strategy_ids || [];
            setSelectedStrats(defaults);
        })
        .catch(err => console.error("Failed to fetch defaults", err))
        .finally(() => setIsReady(true));
    }, []);

    // 2. Fetch stats dynamically whenever the selected strategies change
    useEffect(() => {
        if (!isReady) return;

        const fetchPerformance = async () => {
            setLoadingStats(true);
            try {
                let url = '/dashboard/performance';
    if (selectedStrats.length > 0) {
        url += `?strategy_ids=${selectedStrats.join(',')}`;
    }
    const res = await api.get(url);
    setStats(res.data);
    setError('');
            } catch (err) {
                setError('Failed to load performance statistics.');
                console.error(err);
            } finally {
                setLoadingStats(false);
            }
        };

        fetchPerformance();
    }, [selectedStrats, isReady]);

    if (loadingStats && !stats) return <div style={{ padding: '2rem' }}>Loading Dashboard...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    const StatCard = ({ title, value, prefix = '', suffix = '', isCurrency = false }) => {
        const isPositive = parseFloat(value) >= 0;
        const color = isCurrency ? (isPositive ? '#22c55e' : '#ef4444') : '#f8fafc';
        return (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', flex: 1 }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', color: '#94a3b8', textTransform: 'uppercase' }}>{title}</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: color }}>{prefix}{value}{suffix}</div>
            </div>
        );
    };

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <h2 style={{ margin: 0, color: '#f8fafc' }}>Performance Dashboard</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: '#1e293b', padding: '0.75rem', borderRadius: '8px' }}>
        <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Filter:</span>
        <StrategyPicker selectedIds={selectedStrats} onChange={setSelectedStrats} />
        </div>
        </div>

        {stats && (
            <>
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '3rem' }}>
            <StatCard title="Total Realized P&L" value={stats.total_pnl} prefix={stats.total_pnl > 0 ? '+' : ''} isCurrency={true} />
            <StatCard title="Win Rate" value={stats.win_rate} suffix="%" />
            <StatCard title="Profit Factor" value={stats.profit_factor} />
            <StatCard title="Expectancy" value={stats.expectancy} prefix="$" />
            <StatCard title="Closed Trades" value={stats.total_trades} />
            </div>

            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'stretch' }}>
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', minHeight: '400px', flex: 2, minWidth: '0' }}>
            <h3 style={{ margin: '0 0 2rem 0', color: '#f8fafc' }}>Cumulative Equity Curve</h3>
            {stats.equity_curve?.length > 0 ? (
                <div style={{ width: '100%', height: 350 }}>
                <ResponsiveContainer>
                <LineChart data={stats.equity_curve} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} tickFormatter={(tick) => tick.split(' ')[0]} />
                <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
                <RechartsTooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="cumulative_pnl" stroke="#22d3ee" strokeWidth={3} dot={{ r: 4, fill: '#22d3ee', strokeWidth: 0 }} activeDot={{ r: 6, fill: '#f8fafc' }} />
                </LineChart>
                </ResponsiveContainer>
                </div>
            ) : (
                <p style={{ color: '#94a3b8', textAlign: 'center', marginTop: '4rem' }}>Not enough closed trades to generate an equity curve.</p>
            )}
            </div>
            <NewsPanel />
            </div>

            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginTop: '2rem' }}>
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', flex: 1, minWidth: '300px' }}>
            <h3 style={{ margin: '0 0 1.5rem 0', color: '#f8fafc' }}>P&L by Emotion</h3>
            {stats.emotion_stats?.length > 0 ? (
                <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                <BarChart data={stats.emotion_stats} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <RechartsTooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px' }} itemStyle={{ color: '#f8fafc', fontWeight: 'bold' }} formatter={(value, name, props) => [`$${value}`, `Win Rate: ${props.payload.win_rate}%`]} />
                <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                {stats.emotion_stats.map((entry, idx) => <Cell key={`cell-${idx}`} fill={entry.pnl >= 0 ? '#22c55e' : '#ef4444'} />)}
                </Bar>
                </BarChart>
                </ResponsiveContainer>
                </div>
            ) : <p style={{ color: '#94a3b8', textAlign: 'center' }}>No emotion data logged.</p>}
            </div>

            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', flex: 1, minWidth: '300px' }}>
            <h3 style={{ margin: '0 0 1.5rem 0', color: '#f8fafc' }}>P&L by Setup Tag</h3>
            {stats.tag_stats?.length > 0 ? (
                <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                <BarChart data={stats.tag_stats} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <RechartsTooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px' }} itemStyle={{ color: '#f8fafc', fontWeight: 'bold' }} formatter={(value, name, props) => [`$${value}`, `Win Rate: ${props.payload.win_rate}%`]} />
                <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                {stats.tag_stats.map((entry, idx) => <Cell key={`cell-${idx}`} fill={entry.pnl >= 0 ? '#22d3ee' : '#ef4444'} />)}
                </Bar>
                </BarChart>
                </ResponsiveContainer>
                </div>
            ) : <p style={{ color: '#94a3b8', textAlign: 'center' }}>No setup tags logged.</p>}
            </div>
            </div>
            </>
        )}
        </div>
    );
}
