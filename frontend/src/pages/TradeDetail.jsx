import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../utils/api';
import LivePriceBadge from '../components/LivePriceBadge';
import { useLivePrices } from '../hooks/useLivePrices';

export default function TradeDetail() {
    const { id } = useParams();
    const [trade, setTrade] = useState(null);
    const [strategy, setStrategy] = useState(null);
    const [instrument, setInstrument] = useState(null);
    const [rules, setRules] = useState([]);
    const [attachments, setAttachments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { liveData } = useLivePrices(3);
    const tradeLiveData = liveData[id];

    // Execution / Closure State
    const [isClosing, setIsClosing] = useState(false);
    const [exitPrice, setExitPrice] = useState('');
    const [exitSize, setExitSize] = useState('');
    const [exitNote, setExitNote] = useState('');

    const [isEditingNotes, setIsEditingNotes] = useState(false);
    const [notesText, setNotesText] = useState('');
    const [uploading, setUploading] = useState(false);

    const fetchData = async () => {
        try {
            const tradeRes = await api.get(`/trades/${id}`);
            const t = tradeRes.data;
            setTrade(t);
            setNotesText(t.notes || '');

            const [stratRes, instRes, rulesRes, attachRes] = await Promise.all([
                api.get(`/strategies/`),
                                                                               api.get(`/instruments/`),
                                                                               api.get(`/strategies/${t.strategy_id}/rules`),
                                                                               api.get(`/attachments/trade/${id}`)
            ]);

            setStrategy(stratRes.data.find(s => s.id === t.strategy_id));
            setInstrument(instRes.data.find(i => i.id === t.instrument_id));
            setRules(rulesRes.data);
            setAttachments(attachRes.data);

        } catch (err) {
            setError('Failed to load trade details.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const handleExitExecution = async (e) => {
        e.preventDefault();
        try {
            await api.post(`/trades/${id}/executions`, {
                execution_type: 'exit',
                price: parseFloat(exitPrice),
                           size: parseFloat(exitSize),
                           note: exitNote
            });
            setIsClosing(false);
            setExitPrice('');
            setExitNote('');
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to log execution');
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

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('owner_type', 'trade');
        formData.append('owner_id', id);

        try {
            await api.post('/attachments/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const handleDeleteAttachment = async (attachmentId) => {
        if (!window.confirm("Delete this screenshot?")) return;
        try {
            await api.delete(`/attachments/${attachmentId}`);
            fetchData();
        } catch (err) {
            alert('Failed to delete attachment');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading trade...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;
    if (!trade) return null;

    const isLong = trade.direction === 'long';
    const hasViolations = trade.rule_violations && Object.keys(trade.rule_violations).length > 0;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Link to="/journal" style={{ color: 'var(--text-muted)', textDecoration: 'none', marginBottom: '2rem', display: 'inline-block' }}>
        ← Back to Journal
        </Link>

        {/* Header Section */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-panel)', borderRadius: '8px', borderLeft: `4px solid ${isLong ? '#22c55e' : '#ef4444'}` }}>
        <div>
        <h2 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {instrument?.symbol}
        <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: isLong ? '#22c55e20' : '#ef444420', color: isLong ? '#22c55e' : '#ef4444', textTransform: 'uppercase' }}>
        {trade.direction}
        </span>
        <span style={{ fontSize: '0.875rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: trade.status === 'open' ? '#eab30820' : 'var(--border-color)', color: trade.status === 'open' ? '#eab308' : 'var(--text-primary)', textTransform: 'uppercase' }}>
        {trade.status}
        </span>
        {trade.status === 'open' && <LivePriceBadge liveData={tradeLiveData} isLong={isLong} />}
        </h2>
        <div style={{ color: 'var(--text-muted)' }}>{strategy?.name} • Opened: {new Date(trade.opened_at).toLocaleString()}</div>
        </div>

        <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Realized P&L</div>
        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: trade.pnl_realized >= 0 ? '#22c55e' : '#ef4444' }}>
        {trade.pnl_realized > 0 ? '+' : ''}{trade.pnl_realized !== null ? trade.pnl_realized : '0.00'}
        </div>
        {trade.status === 'closed' ? (
            trade.r_multiple && <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{trade.r_multiple} R</div>
        ) : (
            <Link to={`/journal/${trade.id}/edit`} style={{ display: 'inline-block', marginTop: '0.5rem', background: 'var(--border-color)', color: 'var(--text-primary)', padding: '0.4rem 0.75rem', textDecoration: 'none', borderRadius: '4px', fontSize: '0.75rem' }}>
            Edit Setup
            </Link>
        )}
        </div>
        </div>

        {/* Core Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Entry Price</div>
        <div style={{ fontSize: '1.125rem', color: 'var(--text-primary)' }}>{trade.entry_price}</div>
        </div>
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '8px', border: trade.status === 'open' ? '1px solid var(--accent)' : 'none' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Open Size (Lots)</div>
        <div style={{ fontSize: '1.125rem', color: 'var(--text-primary)', fontWeight: 'bold' }}>{trade.size}</div>
        </div>
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Stop Loss</div>
        <div style={{ fontSize: '1.125rem', color: 'var(--text-primary)' }}>{trade.stop_loss || '—'}</div>
        </div>
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Take Profit</div>
        <div style={{ fontSize: '1.125rem', color: 'var(--text-primary)' }}>{trade.take_profit || '—'}</div>
        </div>
        </div>

        {hasViolations && (
            <div style={{ marginBottom: '2rem', padding: '1.5rem', background: '#451a1a', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>⚠️ Strategy Rule Violations</h3>
            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Object.entries(trade.rule_violations).map(([key, message]) => <li key={key}>{message}</li>)}
            </ul>
            </div>
        )}

        {/* Trade Closure / Scaling Action */}
        {trade.status === 'open' && (
            <div style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--border-color)', borderRadius: '8px' }}>
            {!isClosing ? (
                <button onClick={() => { setIsClosing(true); setExitSize(trade.size); }} style={{ background: '#eab308', color: 'var(--bg-color)', padding: '0.75rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}>
                Log Exit / Scale Out
                </button>
            ) : (
                <form onSubmit={handleExitExecution} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '120px' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Exit Price</label>
                <input type="number" step="any" value={exitPrice} onChange={e => setExitPrice(e.target.value)} required style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '4px' }} />
                </div>
                <div style={{ flex: 1, minWidth: '120px' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Size to Close</label>
                <input type="number" step="any" max={trade.size} value={exitSize} onChange={e => setExitSize(e.target.value)} required style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '4px' }} />
                </div>
                <div style={{ flex: 2, minWidth: '200px' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Note (Optional)</label>
                <input type="text" value={exitNote} onChange={e => setExitNote(e.target.value)} placeholder="e.g. Scaled out at resistance" style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '4px' }} />
                </div>
                <button type="submit" style={{ background: '#22c55e', color: 'var(--text-primary)', padding: '0.75rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px', height: '42px' }}>
                Execute
                </button>
                <button type="button" onClick={() => setIsClosing(false)} style={{ background: 'transparent', color: 'var(--text-secondary)', padding: '0.75rem', border: 'none', cursor: 'pointer', height: '42px' }}>
                Cancel
                </button>
                </form>
            )}
            </div>
        )}

        {/* Execution History */}
        {trade.executions && trade.executions.length > 0 && (
            <div style={{ marginBottom: '2rem', background: 'var(--bg-panel)', borderRadius: '8px', overflow: 'hidden' }}>
            <h3 style={{ margin: 0, padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', color: 'var(--text-primary)' }}>Execution History</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
            <tr style={{ background: 'var(--bg-color)' }}>
            <th style={{ padding: '1rem 1.5rem', color: 'var(--text-muted)' }}>Time</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Type</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Price</th>
            <th style={{ padding: '1rem', color: 'var(--text-muted)' }}>Lots</th>
            <th style={{ padding: '1rem 1.5rem', color: 'var(--text-muted)' }}>Note</th>
            </tr>
            </thead>
            <tbody>
            {trade.executions.map(ex => (
                <tr key={ex.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{new Date(ex.executed_at).toLocaleString()}</td>
                <td style={{ padding: '1rem' }}>
                <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: ex.execution_type === 'entry' ? '#3b82f620' : '#eab30820', color: ex.execution_type === 'entry' ? '#3b82f6' : '#eab308', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 'bold' }}>
                {ex.execution_type}
                </span>
                </td>
                <td style={{ padding: '1rem', color: 'var(--text-primary)', fontWeight: 'bold' }}>{ex.price}</td>
                <td style={{ padding: '1rem', color: 'var(--text-primary)' }}>{ex.size}</td>
                <td style={{ padding: '1rem 1.5rem', color: 'var(--text-muted)' }}>{ex.note || '—'}</td>
                </tr>
            ))}
            </tbody>
            </table>
            </div>
        )}

        {/* Checklist */}
        <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem 0' }}>Strategy Checklist</h3>
        {rules.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No rules defined for this strategy.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {rules.map(rule => {
                const check = trade.condition_checks.find(c => c.rule_id === rule.id);
                return (
                    <div key={rule.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'var(--bg-panel)', borderRadius: '4px' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '4px', background: check ? (check.passed ? '#22c55e' : '#ef4444') : 'var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.8rem' }}>
                    {check ? (check.passed ? '✓' : '✗') : '?'}
                    </div>
                    <div style={{ flex: 1 }}>
                    <div style={{ color: 'var(--text-primary)' }}>{rule.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{rule.rule_type} {rule.is_required ? '(Required)' : ''}</div>
                    </div>
                    </div>
                )
            })}
            </div>
        )}
        </div>

        {/* Notes Section */}
        <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>Trade Notes</h3>
        {!isEditingNotes && (
            <button onClick={() => setIsEditingNotes(true)} style={{ background: 'transparent', color: 'var(--accent)', border: '1px solid var(--accent)', padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer' }}>
            Edit
            </button>
        )}
        </div>
        {isEditingNotes ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <textarea value={notesText} onChange={e => setNotesText(e.target.value)} style={{ width: '100%', minHeight: '150px', padding: '1rem', background: 'var(--bg-color)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }} />
            <div style={{ display: 'flex', gap: '1rem' }}>
            <button onClick={handleSaveNotes} style={{ background: 'var(--accent)', color: 'var(--bg-color)', padding: '0.5rem 1.5rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}>Save Notes</button>
            <button onClick={() => { setIsEditingNotes(false); setNotesText(trade.notes || ''); }} style={{ background: 'transparent', color: 'var(--text-muted)', border: 'none', cursor: 'pointer' }}>Cancel</button>
            </div>
            </div>
        ) : (
            <div style={{ padding: '1.5rem', background: 'var(--bg-panel)', borderRadius: '8px', minHeight: '100px', whiteSpace: 'pre-wrap', color: trade.notes ? 'var(--text-primary)' : 'var(--text-muted)' }}>
            {trade.notes || "No notes recorded for this trade."}
            </div>
        )}
        </div>

        {/* Screenshots Section */}
        <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>Screenshots</h3>
        <div>
        <label style={{ background: 'var(--border-color)', color: 'var(--text-primary)', padding: '0.5rem 1rem', border: 'none', cursor: 'pointer', borderRadius: '4px', display: 'inline-block' }}>
        {uploading ? 'Uploading...' : '+ Add Image'}
        <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} disabled={uploading} />
        </label>
        </div>
        </div>
        {attachments.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No screenshots attached.</p>
        ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
            {attachments.map(att => <AuthImage key={att.id} attachmentId={att.id} onDelete={() => handleDeleteAttachment(att.id)} />)}
            </div>
        )}
        </div>
        </div>
    );
}

function AuthImage({ attachmentId, onDelete }) {
    const [imgSrc, setImgSrc] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchImage = async () => {
            try {
                const response = await api.get(`/attachments/${attachmentId}/file`, { responseType: 'blob' });
                const url = URL.createObjectURL(response.data);
                setImgSrc(url);
            } catch (error) {
                console.error("Failed to load image", error);
            } finally {
                setLoading(false);
            }
        };
        fetchImage();
        return () => { if (imgSrc) URL.revokeObjectURL(imgSrc); };
    }, [attachmentId]);

    if (loading) return <div style={{ background: 'var(--border-color)', padding: '2rem', textAlign: 'center', borderRadius: '8px' }}>Loading...</div>;
    if (!imgSrc) return <div style={{ background: 'var(--border-color)', padding: '2rem', textAlign: 'center', borderRadius: '8px', color: '#ef4444' }}>Error</div>;

    return (
        <div style={{ position: 'relative', background: 'var(--bg-panel)', padding: '0.5rem', borderRadius: '8px' }}>
        <img src={imgSrc} alt="Trade setup" style={{ width: '100%', height: 'auto', borderRadius: '4px', display: 'block', cursor: 'pointer' }} onClick={() => window.open(imgSrc, '_blank')} />
        <button onClick={onDelete} style={{ position: 'absolute', top: '10px', right: '10px', background: 'rgba(0,0,0,0.7)', color: '#ef4444', border: 'none', borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>×</button>
        </div>
    );
}
