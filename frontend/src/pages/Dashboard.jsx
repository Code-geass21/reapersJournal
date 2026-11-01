
import { useState, useEffect } from 'react';
import api from '../utils/api';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    BarChart, Bar, Cell
} from 'recharts';
import NewsPanel from '../components/NewsPanel';

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

    if (loading) {
        return <div style={{ padding: '2rem' }}>Loading Dashboard...</div>;
    }

    if (error) {
        return (
            <div style={{ padding: '2rem', color: '#ef4444' }}>
            {error}
            </div>
        );
    }

    // Helper component for statistic cards
    const StatCard = ({
        title,
        value,
        prefix = '',
        suffix = '',
        isCurrency = false
    }) => {
        const isPositive = parseFloat(value) >= 0;
        const color = isCurrency
        ? (isPositive ? '#22c55e' : '#ef4444')
        : '#f8fafc';

        return (
            <div style={{
                background: '#1e293b',
                padding: '1.5rem',
                borderRadius: '8px',
                flex: 1
            }}>
            <h3 style={{
                margin: '0 0 0.5rem 0',
                fontSize: '0.875rem',
                color: '#94a3b8',
                textTransform: 'uppercase'
            }}>
            {title}
            </h3>

            <div style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: color
            }}>
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
                <div style={{
                    background: '#0f172a',
                    padding: '1rem',
                    border: '1px solid #334155',
                    borderRadius: '4px'
                }}>
                <p style={{
                    color: '#94a3b8',
                    margin: '0 0 0.5rem 0'
                }}>
                {label}
                </p>

                <p style={{
                    color: val >= 0 ? '#22c55e' : '#ef4444',
                    margin: 0,
                    fontWeight: 'bold'
                }}>
                P&L: {val > 0 ? '+' : ''}{val}
                </p>
                </div>
            );
        }

        return null;
    };

    return (
        <div style={{
            padding: '2rem',
            maxWidth: '1200px',
            margin: '0 auto'
        }}>

        {/* Dashboard Header */}
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '2rem'
        }}>
        <h2 style={{
            margin: 0,
            color: '#f8fafc'
        }}>
        Performance Dashboard
        </h2>
        </div>

        {stats && (
            <>
            {/* High-Level Performance Metrics */}
            <div style={{
                display: 'flex',
                gap: '1.5rem',
                flexWrap: 'wrap',
                marginBottom: '3rem'
            }}>
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

            {/* Equity Curve and News Panel Layout */}
            <div style={{
                display: 'flex',
                gap: '2rem',
                flexWrap: 'wrap',
                alignItems: 'stretch'
            }}>

            {/* Cumulative Equity Curve */}
            <div style={{
                background: '#1e293b',
                padding: '2rem',
                borderRadius: '8px',
                minHeight: '400px',
                flex: 2,
                minWidth: '0'
            }}>
            <h3 style={{
                margin: '0 0 2rem 0',
                color: '#f8fafc'
            }}>
            Cumulative Equity Curve
            </h3>

            {stats.equity_curve &&
                stats.equity_curve.length > 0 ? (
                    <div style={{
                        width: '100%',
                        height: 350
                    }}>
                    <ResponsiveContainer>
                    <LineChart
                    data={stats.equity_curve}
                    margin={{
                        top: 5,
                        right: 20,
                        bottom: 5,
                        left: 0
                    }}
                    >
                    <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                    vertical={false}
                    />

                    <XAxis
                    dataKey="date"
                    stroke="#94a3b8"
                    tick={{ fill: '#94a3b8' }}
                    tickFormatter={(tick) =>
                        tick.split(' ')[0]
                    }
                    />

                    <YAxis
                    stroke="#94a3b8"
                    tick={{ fill: '#94a3b8' }}
                    />

                    <RechartsTooltip
                    content={<CustomTooltip />}
                    />

                    <Line
                    type="monotone"
                    dataKey="cumulative_pnl"
                    stroke="#22d3ee"
                    strokeWidth={3}
                    dot={{
                        r: 4,
                        fill: '#22d3ee',
                        strokeWidth: 0
                    }}
                    activeDot={{
                        r: 6,
                        fill: '#f8fafc'
                    }}
                    />
                    </LineChart>
                    </ResponsiveContainer>
                    </div>
                ) : (
                    <p style={{
                        color: '#94a3b8',
                        textAlign: 'center',
                        marginTop: '4rem'
                    }}>
                    Not enough closed trades to generate an equity curve.
                    </p>
                )}
                </div>

                {/* News Panel */}
                <NewsPanel />

                </div>

                {/* Analytics Breakdown Row */}
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginTop: '2rem' }}>

                {/* Emotion Analytics */}
                <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', flex: 1, minWidth: '300px' }}>
                    <h3 style={{ margin: '0 0 1.5rem 0', color: '#f8fafc' }}>P&L by Emotion</h3>
                    {stats.emotion_stats && stats.emotion_stats.length > 0 ? (
                        <div style={{ width: '100%', height: 250 }}>
                            <ResponsiveContainer>
                                <BarChart data={stats.emotion_stats} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 30 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                    <XAxis type="number" stroke="#94a3b8" />
                                    <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <RechartsTooltip
                                        contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px' }}
                                        itemStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                                        formatter={(value, name, props) => [`$${value}`, `Win Rate: ${props.payload.win_rate}%`]}
                                    />
                                    <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                                        {stats.emotion_stats.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#22c55e' : '#ef4444'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <p style={{ color: '#94a3b8', textAlign: 'center' }}>No emotion data logged.</p>
                    )}
                </div>

                {/* Setup Tags Analytics */}
                <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', flex: 1, minWidth: '300px' }}>
                    <h3 style={{ margin: '0 0 1.5rem 0', color: '#f8fafc' }}>P&L by Setup Tag</h3>
                    {stats.tag_stats && stats.tag_stats.length > 0 ? (
                        <div style={{ width: '100%', height: 250 }}>
                            <ResponsiveContainer>
                                <BarChart data={stats.tag_stats} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                    <XAxis type="number" stroke="#94a3b8" />
                                    <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <RechartsTooltip
                                        contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px' }}
                                        itemStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                                        formatter={(value, name, props) => [`$${value}`, `Win Rate: ${props.payload.win_rate}%`]}
                                    />
                                    <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                                        {stats.tag_stats.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#22d3ee' : '#ef4444'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <p style={{ color: '#94a3b8', textAlign: 'center' }}>No setup tags logged.</p>
                    )}
                </div>
            </div>
                </>
        )}
        </div>
    );
}
