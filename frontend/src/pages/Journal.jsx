import { useState, useEffect } from 'react';
import api from '../utils/api';
import { Link } from 'react-router-dom';
import LivePriceBadge from '../components/LivePriceBadge';
import { useLivePrices } from '../hooks/useLivePrices';

export default function Journal() {
    const [trades, setTrades] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Filters
    const [filterStrategy, setFilterStrategy] = useState('');
    const [filterStatus, setFilterStatus] = useState('');

    const { liveData } = useLivePrices(3);

    // Fetch master data once
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [stratRes, instRes] = await Promise.all([
                    api.get('/strategies/'),
                                                              api.get('/instruments/')
                ]);
                setStrategies(stratRes.data);
                setInstruments(instRes.data);
            } catch (err) {
                console.error("Failed to load core data", err);
            }
        };
        loadInitialData();
    }, []);

    // Fetch trades dynamically based on filters
    useEffect(() => {
        const fetchTrades = async () => {
            setLoading(true);
            try {
                let url = '/trades/';
                const params = new URLSearchParams();
                if (filterStrategy) params.append('strategy_id', filterStrategy);
                if (filterStatus) params.append('status', filterStatus);
                if (params.toString()) url += `?${params.toString()}`;

                const tradesRes = await api.get(url);
                setTrades(tradesRes.data);
                setError('');
            } catch (err) {
                setError('Failed to load journal data.');
            } finally {
                setLoading(false);
            }
        };
        fetchTrades();
    }, [filterStrategy, filterStatus]);

    const handleDelete = async (tradeId) => {
        if (!window.confirm("Delete this trade? This cannot be undone.")) return;
        try {
            await api.delete(`/trades/${tradeId}`);
            setTrades(trades.filter(t => t.id !== tradeId));
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to delete trade');
        }
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Trading Journal</h2>
        <Link
        to="/journal/new"
        style={{ background: 'var(--accent)', color: 'var(--bg-color)', padding: '0.5rem 1rem', textDecoration: 'none', fontWeight: 'bold', borderRadius: '4px' }}
        >
        + New Trade
        </Link>
        </div>

        {/* NEW: Filter Bar */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', background: 'var(--bg-panel)', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Strategy</label>
        <select value={filterStrategy} onChange={e => setFilterStrategy(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px' }}>
        <option value="">All Strategies</option>
        {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Status</label>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px' }}>
        <option value="">All Statuses</option>
        <option value="open">Open</option>
        <option value="closed">Closed</option>
        <option value="cancelled">Cancelled</option>
        </select>
        </div>
        </div>

        {error && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

        {loading ? (
            <div style={{ color: 'var(--text-muted)' }}>Loading trades...</div>
        ) : trades.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No trades match your filters.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {trades.map(trade => {
                const strat = strategies.find(s => s.id === trade.strategy_id);
                const inst = instruments.find(i => i.id === trade.instrument_id);
                const isLong = trade.direction === 'long';
                const tradeLiveData = liveData[trade.id];

                return (
                    <div key={trade.id} style={{ background: 'var(--bg-panel)', padding: '1.25rem', borderRadius: '8px', borderLeft: `4px solid ${isLong ? '#22c55e' : '#ef4444'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                    <h3 style={{ margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Link to={`/journal/${trade.id}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                    {inst?.symbol || 'Unknown'} →
                    </Link>
                    <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: isLong ? '#22c55e20' : '#ef444420', color: isLong ? '#22c55e' : '#ef4444', textTransform: 'uppercase' }}>
                    {trade.direction}
                    </span>
                    {trade.status === 'open' && (
                        <LivePriceBadge liveData={tradeLiveData} isLong={isLong} />
                    )}
                    </h3>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{strat?.name || 'Unknown Strategy'} • Opened: {new Date(trade.opened_at).toLocaleString()}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: trade.status === 'open' ? '#eab30820' : 'var(--border-color)', color: trade.status === 'open' ? '#eab308' : 'var(--text-primary)', textTransform: 'uppercase' }}>
                    {trade.status}
                    </span>
                    <button onClick={() => handleDelete(trade.id)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem', padding: 0 }} title="Delete Trade">
                    ×
                    </button>
                    </div>
                    </div>
                    <div style={{ display: 'flex', gap: '2rem', fontSize: '0.875rem' }}>
                    <div><span style={{ color: 'var(--text-muted)' }}>Entry:</span> {trade.entry_price}</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Size:</span> {trade.size}</div>
                    {trade.stop_loss && <div><span style={{ color: 'var(--text-muted)' }}>SL:</span> {trade.stop_loss}</div>}
                    {trade.take_profit && <div><span style={{ color: 'var(--text-muted)' }}>TP:</span> {trade.take_profit}</div>}
                    </div>
                    </div>
                )
            })}
            </div>
        )}
        </div>
    );
}
