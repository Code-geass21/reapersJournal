import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../utils/api';

export default function TradeDetail() {
    const { id } = useParams();
    const [trade, setTrade] = useState(null);
    const [strategy, setStrategy] = useState(null);
    const [instrument, setInstrument] = useState(null);
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Trade Closure State
    const [isClosing, setIsClosing] = useState(false);
    const [exitPrice, setExitPrice] = useState('');

    // Notes Update State
    const [isEditingNotes, setIsEditingNotes] = useState(false);
    const [notesText, setNotesText] = useState('');

    const fetchData = async () => {
        try {
            const tradeRes = await api.get(`/trades/${id}`);
            const t = tradeRes.data;
            setTrade(t);
            setNotesText(t.notes || '');

            const [stratRes, instRes, rulesRes] = await Promise.all([
                api.get(`/strategies/`),
                                                                    api.get(`/instruments/`),
                                                                    api.get(`/strategies/${t.strategy_id}/rules`)
            ]);

            setStrategy(stratRes.data.find(s => s.id === t.strategy_id));
            setInstrument(instRes.data.find(i => i.id === t.instrument_id));
            setRules(rulesRes.data);

        } catch (err) {
            setError('Failed to load trade details.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const handleCloseTrade = async (e) => {
        e.preventDefault();
        try {
            await api.put(`/trades/${id}`, {
                status: 'closed',
                exit_price: parseFloat(exitPrice)
            });
            setIsClosing(false);
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to close trade');
        }
    };

    const handleSaveNotes = async () => {
        try {
            await api.put(`/trades/${id}`, { notes: notesText });
            setIsEditingNotes(false);
            fetchData();
        } catch (err) {
            alert('Failed to save notes');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading trade...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;
    if (!trade) return null;

    const isLong = trade.direction === 'long';

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Link to="/journal" style={{ color: '#94a3b8', textDecoration: 'none', marginBottom: '2rem', display: 'inline-block' }}>
        ← Back to Journal
        </Link>

        {/* Header Section */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', padding: '1.5rem', background: '#1e293b', borderRadius: '8px', borderLeft: `4px solid ${isLong ? '#22c55e' : '#ef4444'}` }}>
        <div>
        <h2 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {instrument?.symbol}
        <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: isLong ? '#22c55e20' : '#ef444420', color: isLong ? '#22c55e' : '#ef4444', textTransform: 'uppercase' }}>
        {trade.direction}
        </span>
        <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: trade.status === 'open' ? '#eab30820' : '#334155', color: trade.status === 'open' ? '#eab308' : '#f8fafc', textTransform: 'uppercase' }}>
        {trade.status}
        </span>
        </h2>
        <div style={{ color: '#94a3b8' }}>{strategy?.name} • Opened: {new Date(trade.opened_at).toLocaleString()}</div>
        </div>

        {/* P&L Display (If Closed) */}
        {trade.status === 'closed' && (
            <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Realized P&L</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: trade.pnl_realized >= 0 ? '#22c55e' : '#ef4444' }}>
            {trade.pnl_realized > 0 ? '+' : ''}{trade.pnl_realized}
            </div>
            {trade.r_multiple && (
                <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>{trade.r_multiple} R</div>
            )}
            </div>
        )}
        </div>

        {/* Core Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Entry Price</div>
        <div style={{ fontSize: '1.125rem', color: '#f8fafc' }}>{trade.entry_price}</div>
        </div>
        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Size (Lots)</div>
        <div style={{ fontSize: '1.125rem', color: '#f8fafc' }}>{trade.size}</div>
        </div>
        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Stop Loss</div>
        <div style={{ fontSize: '1.125rem', color: '#f8fafc' }}>{trade.stop_loss || '—'}</div>
        </div>
        <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Take Profit</div>
        <div style={{ fontSize: '1.125rem', color: '#f8fafc' }}>{trade.take_profit || '—'}</div>
        </div>
        </div>

        {/* Trade Closure Action */}
        {trade.status === 'open' && (
            <div style={{ marginBottom: '2rem', padding: '1.5rem', background: '#334155', borderRadius: '8px' }}>
            {!isClosing ? (
                <button
                onClick={() => setIsClosing(true)}
                style={{ background: '#eab308', color: '#0f172a', padding: '0.75rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}
                >
                Close Position
                </button>
            ) : (
                <form onSubmit={handleCloseTrade} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#f8fafc' }}>Exit Price</label>
                <input
                type="number"
                step="any"
                value={exitPrice}
                onChange={e => setExitPrice(e.target.value)}
                required
                style={{ width: '100%', padding: '0.75rem' }}
                />
                </div>
                <button type="submit" style={{ background: '#22c55e', color: '#f8fafc', padding: '0.75rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}>
                Confirm Close
                </button>
                <button type="button" onClick={() => setIsClosing(false)} style={{ background: 'transparent', color: '#cbd5e1', padding: '0.75rem', border: 'none', cursor: 'pointer' }}>
                Cancel
                </button>
                </form>
            )}
            </div>
        )}

        {/* Rule Checklist (Phase 3 Core Feature) */}
        <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem 0' }}>Strategy Checklist</h3>
        {rules.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No rules defined for this strategy.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {rules.map(rule => {
                const check = trade.condition_checks.find(c => c.rule_id === rule.id);
                return (
                    <div key={rule.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: '#1e293b', borderRadius: '4px' }}>
                    <div style={{
                        width: '24px', height: '24px', borderRadius: '4px',
                        background: check ? (check.passed ? '#22c55e' : '#ef4444') : '#334155',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.8rem'
                    }}>
                    {check ? (check.passed ? '✓' : '✗') : '?'}
                    </div>
                    <div style={{ flex: 1 }}>
                    <div style={{ color: '#f8fafc' }}>{rule.label}</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>{rule.rule_type} {rule.is_required ? '(Required)' : ''}</div>
                    </div>
                    </div>
                )
            })}
            </div>
        )}
        </div>

        {/* Notes Section */}
        <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>Trade Notes</h3>
        {!isEditingNotes && (
            <button onClick={() => setIsEditingNotes(true)} style={{ background: 'transparent', color: '#22d3ee', border: '1px solid #22d3ee', padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer' }}>
            Edit
            </button>
        )}
        </div>

        {isEditingNotes ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <textarea
            value={notesText}
            onChange={e => setNotesText(e.target.value)}
            style={{ width: '100%', minHeight: '150px', padding: '1rem', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' }}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
            <button onClick={handleSaveNotes} style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}>Save Notes</button>
            <button onClick={() => { setIsEditingNotes(false); setNotesText(trade.notes || ''); }} style={{ background: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer' }}>Cancel</button>
            </div>
            </div>
        ) : (
            <div style={{ padding: '1.5rem', background: '#1e293b', borderRadius: '8px', minHeight: '100px', whiteSpace: 'pre-wrap', color: trade.notes ? '#f8fafc' : '#94a3b8' }}>
            {trade.notes || "No notes recorded for this trade."}
            </div>
        )}
        </div>

        </div>
    );
}
