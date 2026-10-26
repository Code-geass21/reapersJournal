import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function Journal() {
    const [trades, setTrades] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isFormOpen, setIsFormOpen] = useState(false);

    // Trade form state
    const [newTrade, setNewTrade] = useState({
        strategy_id: '',
        instrument_id: '',
        direction: 'long',
        entry_price: '',
        size: '',
        stop_loss: '',
        take_profit: '',
        notes: ''
    });

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

            // Set defaults for the form if data exists
            if (stratRes.data.length > 0 && newTrade.strategy_id === '') {
                setNewTrade(prev => ({ ...prev, strategy_id: stratRes.data[0].id }));
            }
            if (instRes.data.length > 0 && newTrade.instrument_id === '') {
                setNewTrade(prev => ({ ...prev, instrument_id: instRes.data[0].id }));
            }
        } catch (err) {
            setError('Failed to load journal data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateTrade = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                strategy_id: parseInt(newTrade.strategy_id),
                instrument_id: parseInt(newTrade.instrument_id),
                direction: newTrade.direction,
                entry_price: parseFloat(newTrade.entry_price),
                size: parseFloat(newTrade.size),
                stop_loss: newTrade.stop_loss ? parseFloat(newTrade.stop_loss) : null,
                take_profit: newTrade.take_profit ? parseFloat(newTrade.take_profit) : null,
                notes: newTrade.notes || null,
                condition_checks: [] // We will implement the checklist UI later
            };

            await api.post('/trades/', payload);
            setIsFormOpen(false);
            setNewTrade({ ...newTrade, entry_price: '', size: '', stop_loss: '', take_profit: '', notes: '' });
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to log trade');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading Journal...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>Trading Journal</h2>
        <button
        onClick={() => setIsFormOpen(!isFormOpen)}
        style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}
        >
        {isFormOpen ? 'Cancel' : '+ New Trade'}
        </button>
        </div>

        {isFormOpen && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <form onSubmit={handleCreateTrade} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Strategy</label>
            <select
            value={newTrade.strategy_id}
            onChange={e => setNewTrade({...newTrade, strategy_id: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            required
            >
            {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Instrument</label>
            <select
            value={newTrade.instrument_id}
            onChange={e => setNewTrade({...newTrade, instrument_id: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            required
            >
            {instruments.map(i => <option key={i.id} value={i.id}>{i.symbol}</option>)}
            </select>
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Direction</label>
            <select
            value={newTrade.direction}
            onChange={e => setNewTrade({...newTrade, direction: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            >
            <option value="long">Long</option>
            <option value="short">Short</option>
            </select>
            </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Entry Price</label>
            <input type="number" step="any" value={newTrade.entry_price} onChange={e => setNewTrade({...newTrade, entry_price: e.target.value})} required style={{ width: '100%', padding: '0.5rem' }} />
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Position Size (Lots)</label>
            <input type="number" step="any" value={newTrade.size} onChange={e => setNewTrade({...newTrade, size: e.target.value})} required style={{ width: '100%', padding: '0.5rem' }} />
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Stop Loss</label>
            <input type="number" step="any" value={newTrade.stop_loss} onChange={e => setNewTrade({...newTrade, stop_loss: e.target.value})} style={{ width: '100%', padding: '0.5rem' }} />
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Take Profit</label>
            <input type="number" step="any" value={newTrade.take_profit} onChange={e => setNewTrade({...newTrade, take_profit: e.target.value})} style={{ width: '100%', padding: '0.5rem' }} />
            </div>
            </div>

            <div>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Notes</label>
            <textarea value={newTrade.notes} onChange={e => setNewTrade({...newTrade, notes: e.target.value})} style={{ width: '100%', padding: '0.5rem', minHeight: '80px' }} />
            </div>

            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', marginTop: '0.5rem' }}>
            Log Trade
            </button>
            </form>
            </div>
        )}

        {trades.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No trades logged yet.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {trades.map(trade => {
                const strat = strategies.find(s => s.id === trade.strategy_id);
                const inst = instruments.find(i => i.id === trade.instrument_id);
                const isLong = trade.direction === 'long';

                return (
                    <div key={trade.id} style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '8px', borderLeft: `4px solid ${isLong ? '#22c55e' : '#ef4444'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                    <h3 style={{ margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {inst?.symbol || 'Unknown'}
                    <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: isLong ? '#22c55e20' : '#ef444420', color: isLong ? '#22c55e' : '#ef4444', textTransform: 'uppercase' }}>
                    {trade.direction}
                    </span>
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
