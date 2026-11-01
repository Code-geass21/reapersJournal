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

    const { liveData } = useLivePrices(30);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [tradesRes, stratRes, instRes] = await Promise.all([
                    api.get('/trades/'),
                                                                         api.get('/strategies/'),
                                                                         api.get('/instruments/')
                ]);
                setTrades(tradesRes.data);
                setStrategies(stratRes.data);
                setInstruments(instRes.data);
            } catch (err) {
                setError('Failed to load journal data.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return <div style={{ padding: '2rem' }}>Loading Journal...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>Trading Journal</h2>
        <Link
        to="/journal/new"
        style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', textDecoration: 'none', fontWeight: 'bold', borderRadius: '4px' }}
        >
        + New Trade
        </Link>
        </div>

        {trades.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No trades logged yet.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {trades.map(trade => {
                const strat = strategies.find(s => s.id === trade.strategy_id);
                const inst = instruments.find(i => i.id === trade.instrument_id);
                const isLong = trade.direction === 'long';
                const tradeLiveData = liveData[trade.id];

                return (
                    <div key={trade.id} style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '8px', borderLeft: `4px solid ${isLong ? '#22c55e' : '#ef4444'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                    <h3 style={{ margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Link to={`/journal/${trade.id}`} style={{ color: '#22d3ee', textDecoration: 'none' }}>
                    {inst?.symbol || 'Unknown'} →
                    </Link>
                    <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: isLong ? '#22c55e20' : '#ef444420', color: isLong ? '#22c55e' : '#ef4444', textTransform: 'uppercase' }}>
                    {trade.direction}
                    </span>
                    {trade.status === 'open' && (
                        <LivePriceBadge liveData={tradeLiveData} isLong={isLong} />
                    )}
                    </h3>
                    <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{strat?.name || 'Unknown Strategy'} • Opened: {new Date(trade.opened_at).toLocaleString()}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: trade.status === 'open' ? '#eab30820' : '#334155', color: trade.status === 'open' ? '#eab308' : '#f8fafc', textTransform: 'uppercase' }}>
                    {trade.status}
                    </span>
                    </div>
                    </div>
                    <div style={{ display: 'flex', gap: '2rem', fontSize: '0.875rem' }}>
                    <div><span style={{ color: '#94a3b8' }}>Entry:</span> {trade.entry_price}</div>
                    <div><span style={{ color: '#94a3b8' }}>Size:</span> {trade.size}</div>
                    {trade.stop_loss && <div><span style={{ color: '#94a3b8' }}>SL:</span> {trade.stop_loss}</div>}
                    {trade.take_profit && <div><span style={{ color: '#94a3b8' }}>TP:</span> {trade.take_profit}</div>}
                    </div>
                    </div>
                )
            })}
            </div>
        )}
        </div>
    );
}
