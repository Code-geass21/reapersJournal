import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../utils/api';
import ConditionChecklist from '../components/ConditionChecklist';
import MarketPicker from '../components/MarketPicker';

export default function TradeForm() {
    const navigate = useNavigate();
    const { id } = useParams();
    const [strategies, setStrategies] = useState([]);
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [conditionChecks, setConditionChecks] = useState([]);

    const [trade, setTrade] = useState({
        strategy_id: '',
        instrument_id: '',
        market: 'FOREX',
        direction: 'long',
        entry_price: '',
        size: '',
        stop_loss: '',
        take_profit: '',
        notes: '',
        tags: '',
        emotion: ''
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [stratRes, instRes] = await Promise.all([
                    api.get('/strategies/'),
                                                              api.get('/instruments/')
                ]);
                setStrategies(stratRes.data);
                setInstruments(instRes.data);

                if (id) {
                    const tradeRes = await api.get(`/trades/${id}`);
                    const t = tradeRes.data;

                    // Look up the market based on the instrument_id
                    const inst = instRes.data.find(i => i.id === t.instrument_id);
                    const marketCode = inst ? inst.market_code : 'FOREX';

    setTrade({
        ...t,
        market: marketCode,
        tags: t.tags ? t.tags.join(', ') : '',
             stop_loss: t.stop_loss || '',
             take_profit: t.take_profit || '',
             notes: t.notes || '',
             emotion: t.emotion || ''
    });
    setConditionChecks(t.condition_checks || []);
                } else {
                    if (stratRes.data.length > 0) {
                        setTrade(prev => ({ ...prev, strategy_id: stratRes.data[0].id }));
                    }
                    if (instRes.data.length > 0) {
                        setTrade(prev => ({ ...prev, instrument_id: instRes.data[0].id }));
                    }
                }
            } catch (err) {
                setError('Failed to load form data.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                strategy_id: parseInt(trade.strategy_id),
                instrument_id: parseInt(trade.instrument_id),
                direction: trade.direction,
                entry_price: parseFloat(trade.entry_price),
                size: parseFloat(trade.size),
                stop_loss: trade.stop_loss ? parseFloat(trade.stop_loss) : null,
                take_profit: trade.take_profit ? parseFloat(trade.take_profit) : null,
                notes: trade.notes || null,
                tags: trade.tags ? trade.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
                emotion: trade.emotion || null,
            };

            if (id) {
                await api.put(`/trades/${id}`, payload);
            } else {
                payload.condition_checks = conditionChecks;
                await api.post('/trades/', payload);
            }
            navigate('/journal');
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to save trade');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    const filteredInstruments = instruments.filter(i => i.market_code === trade.market);

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '2rem' }}>{id ? 'Edit Trade' : 'Log New Trade'}</h2>

        <form onSubmit={handleSubmit} style={{ background: 'var(--bg-panel)', padding: '2rem', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Market</label>
        <MarketPicker value={trade.market} onChange={val => setTrade({ ...trade, market: val })} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Instrument</label>
        <select
        value={trade.instrument_id}
        onChange={e => setTrade({ ...trade, instrument_id: e.target.value })}
        style={{ width: '100%', padding: '0.5rem' }}
        required
        >
        {filteredInstruments.map(i => <option key={i.id} value={i.id}>{i.symbol}</option>)}
        </select>
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Strategy</label>
        <select
        value={trade.strategy_id}
        onChange={e => setTrade({ ...trade, strategy_id: e.target.value })}
        style={{ width: '100%', padding: '0.5rem' }}
        required
        >
        {strategies.filter(s => s.is_active).map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Direction</label>
        <select
        value={trade.direction}
        onChange={e => setTrade({ ...trade, direction: e.target.value })}
        style={{ width: '100%', padding: '0.5rem' }}
        >
        <option value="long">Long</option>
        <option value="short">Short</option>
        </select>
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Entry Price</label>
        <input type="number" step="any" value={trade.entry_price} onChange={e => setTrade({ ...trade, entry_price: e.target.value })} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Position Size (Lots)</label>
        <input type="number" step="any" value={trade.size} onChange={e => setTrade({ ...trade, size: e.target.value })} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Stop Loss</label>
        <input type="number" step="any" value={trade.stop_loss} onChange={e => setTrade({ ...trade, stop_loss: e.target.value })} style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Take Profit</label>
        <input type="number" step="any" value={trade.take_profit} onChange={e => setTrade({ ...trade, take_profit: e.target.value })} style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Tags (comma separated)</label>
        <input type="text" value={trade.tags} onChange={e => setTrade({ ...trade, tags: e.target.value })} placeholder="e.g., FOMC, trendline bounce" style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Emotion</label>
        <select value={trade.emotion} onChange={e => setTrade({ ...trade, emotion: e.target.value })} style={{ width: '100%', padding: '0.5rem' }}>
        <option value="">-- Select --</option>
        <option value="calm">Calm / Neutral</option>
        <option value="anxious">Anxious</option>
        <option value="fomo">FOMO</option>
        <option value="overconfident">Overconfident</option>
        <option value="frustrated">Frustrated / Revenge</option>
        </select>
        </div>
        </div>

        <div>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Notes</label>
        <textarea value={trade.notes} onChange={e => setTrade({ ...trade, notes: e.target.value })} style={{ width: '100%', padding: '0.5rem', minHeight: '100px' }} />
        </div>

        {!id && (
            <ConditionChecklist strategyId={trade.strategy_id} onChecksChange={setConditionChecks} />
        )}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
        <button type="submit" style={{ background: 'var(--accent)', color: 'var(--bg-color)', padding: '0.75rem 1.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px' }}>
        {id ? 'Update Trade' : 'Log Trade'}
        </button>
        <button type="button" onClick={() => navigate('/journal')} style={{ background: 'transparent', color: 'var(--text-muted)', padding: '0.75rem 1.5rem', border: '1px solid var(--border-color)', cursor: 'pointer', borderRadius: '4px' }}>
        Cancel
        </button>
        </div>
        </form>
        </div>
    );
}
