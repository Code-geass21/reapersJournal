import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../utils/api';
import ConditionChecklist from '../components/ConditionChecklist';
import StrategyPicker from '../components/StrategyPicker';
import MarketPicker from '../components/MarketPicker';

export default function TradeForm() {
    const navigate = useNavigate();
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [conditionChecks, setConditionChecks] = useState([]);

    const [newTrade, setNewTrade] = useState({
        strategy_id: '',
        instrument_id: '',
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
        const fetchInstruments = async () => {
            try {
                const res = await api.get('/instruments/');
                setInstruments(res.data);
                if (res.data.length > 0) {
                    setNewTrade(prev => ({ ...prev, instrument_id: res.data[0].id }));
                }
            } catch (err) {
                console.error("Failed to load instruments", err);
            } finally {
                setLoading(false);
            }
        };
        fetchInstruments();
    }, []);

    const handleSubmit = async (e) => {
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
                tags: newTrade.tags ? newTrade.tags.split(',').map(t => t.trim()) : [],
                emotion: newTrade.emotion || null,
                condition_checks: conditionChecks
            };

            await api.post('/trades/', payload);
            navigate('/journal'); // Redirect back to journal on success
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to log trade');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading Form...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Link to="/journal" style={{ color: '#94a3b8', textDecoration: 'none', marginBottom: '2rem', display: 'inline-block' }}>
        ← Back to Journal
        </Link>

        <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px' }}>
        <h2 style={{ margin: '0 0 1.5rem 0', color: '#f8fafc' }}>Log New Execution</h2>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <MarketPicker value="FOREX" onChange={() => {}} />
        </div>
        <div style={{ flex: 1 }}>
        <StrategyPicker
        value={newTrade.strategy_id}
        onChange={(val) => setNewTrade({...newTrade, strategy_id: val})}
        />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Instrument</label>
        <select
        value={newTrade.instrument_id}
        onChange={e => setNewTrade({...newTrade, instrument_id: e.target.value})}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }}
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
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }}
        >
        <option value="long">Long</option>
        <option value="short">Short</option>
        </select>
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Position Size (Lots)</label>
        <input type="number" step="any" value={newTrade.size} onChange={e => setNewTrade({...newTrade, size: e.target.value})} required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Entry Price</label>
        <input type="number" step="any" value={newTrade.entry_price} onChange={e => setNewTrade({...newTrade, entry_price: e.target.value})} required style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Stop Loss</label>
        <input type="number" step="any" value={newTrade.stop_loss} onChange={e => setNewTrade({...newTrade, stop_loss: e.target.value})} style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Take Profit</label>
        <input type="number" step="any" value={newTrade.take_profit} onChange={e => setNewTrade({...newTrade, take_profit: e.target.value})} style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Tags (comma separated)</label>
        <input type="text" value={newTrade.tags} onChange={e => setNewTrade({...newTrade, tags: e.target.value})} placeholder="e.g., FOMC, trendline bounce" style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Emotion</label>
        <select value={newTrade.emotion} onChange={e => setNewTrade({...newTrade, emotion: e.target.value})} style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }}>
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
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Notes</label>
        <textarea value={newTrade.notes} onChange={e => setNewTrade({...newTrade, notes: e.target.value})} style={{ width: '100%', padding: '0.5rem', minHeight: '80px', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }} />
        </div>

        <ConditionChecklist
        strategyId={newTrade.strategy_id}
        onChecksChange={setConditionChecks}
        />

        <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.75rem', fontSize: '1rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', marginTop: '1rem' }}>
        Log Trade
        </button>
        </form>
        </div>
        </div>
    );
}
