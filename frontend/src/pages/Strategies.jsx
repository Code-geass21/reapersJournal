import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';

export default function Strategies() {
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formState, setFormState] = useState({
        name: '',
        description: '',
        market: 'FOREX',
        funding_mode: 'non_systematic',
        sip_amount: '',
        sip_frequency: 'monthly',
    });

    const fetchStrategies = async () => {
        try {
            const res = await api.get('/strategies/');
            setStrategies(res.data);
        } catch (err) {
            setError('Failed to load strategies.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStrategies();
    }, []);

    const resetForm = () => {
        setIsFormOpen(false);
        setEditingId(null);
        setFormState({ name: '', description: '', market: 'FOREX', funding_mode: 'non_systematic', sip_amount: '', sip_frequency: 'monthly' });
    }

    const handleEditClick = (strategy) => {
        setFormState({
            name: strategy.name,
            description: strategy.description || '',
            market: strategy.market,
            funding_mode: strategy.funding_mode,
            sip_amount: strategy.sip_amount || '',
            sip_frequency: strategy.sip_frequency || 'monthly',
        });
        setEditingId(strategy.id);
        setIsFormOpen(true);
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...formState };
            if (!payload.sip_amount) payload.sip_amount = null;

            if (editingId) {
                await api.put(`/strategies/${editingId}`, payload);
            } else {
                await api.post('/strategies/', payload);
            }
            resetForm();
            fetchStrategies();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to save strategy');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this strategy? If it has existing trades, it will be archived instead to preserve your journal history.")) return;
        try {
            await api.delete(`/strategies/${id}`);
            fetchStrategies();
        } catch (err) {
            alert('Failed to delete strategy');
        }
    }

    if (loading) return <div style={{ padding: '2rem' }}>Loading strategies...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>My Strategies</h2>
        <button
        onClick={() => isFormOpen ? resetForm() : setIsFormOpen(true)}
        style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}
        >
        {isFormOpen ? 'Cancel' : '+ New Strategy'}
        </button>
        </div>

        {error && <p style={{ color: '#ef4444' }}>{error}</p>}

        {isFormOpen && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <input
            placeholder="Strategy Name (e.g., London Breakout)"
            value={formState.name}
            onChange={e => setFormState({...formState, name: e.target.value})}
            required
            style={{ padding: '0.5rem' }}
            />
            <textarea
            placeholder="Description"
            value={formState.description}
            onChange={e => setFormState({...formState, description: e.target.value})}
            style={{ padding: '0.5rem', minHeight: '80px' }}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Market</label>
            <select
            value={formState.market}
            onChange={e => setFormState({...formState, market: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            >
            <option value="FOREX">Forex</option>
            </select>
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Funding Mode</label>
            <select
            value={formState.funding_mode}
            onChange={e => setFormState({...formState, funding_mode: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            >
            <option value="non_systematic">Non-Systematic (Manual)</option>
            <option value="systematic">Systematic (SIP/Recurring)</option>
            </select>
            </div>
            </div>

            {formState.funding_mode === 'systematic' && (
                <div style={{ display: 'flex', gap: '1rem' }}>
                <input
                type="number"
                placeholder="SIP Amount"
                value={formState.sip_amount}
                onChange={e => setFormState({...formState, sip_amount: e.target.value})}
                style={{ flex: 1, padding: '0.5rem' }}
                required
                />
                <select
                value={formState.sip_frequency}
                onChange={e => setFormState({...formState, sip_frequency: e.target.value})}
                style={{ flex: 1, padding: '0.5rem' }}
                >
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                </select>
                </div>
            )}

            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', marginTop: '0.5rem', borderRadius: '4px' }}>
            {editingId ? 'Update Strategy' : 'Save Strategy'}
            </button>
            </form>
            </div>
        )}

        {strategies.length === 0 && !isFormOpen ? (
            <p style={{ color: '#94a3b8' }}>You haven't created any strategies yet.</p>
        ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
            {strategies.map(s => (
                <div key={s.id} style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #22d3ee' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                <h3 style={{ margin: '0 0 0.5rem 0' }}>
                <Link to={`/strategies/${s.id}`} style={{ color: s.is_active ? '#f8fafc' : '#94a3b8', textDecoration: 'none' }}>
                {s.name} {!s.is_active && <span style={{fontSize: '0.8rem', fontWeight: 'normal'}}>(Archived)</span>} →
                </Link>
                </h3>
                {s.description && <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1' }}>{s.description}</p>}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleEditClick(s)} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', cursor: 'pointer', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Edit</button>
                <button onClick={() => handleDelete(s.id)} style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', cursor: 'pointer', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Delete</button>
                </div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem', color: '#94a3b8' }}>
                <span><strong>Market:</strong> {s.market}</span>
                <span><strong>Mode:</strong> {s.funding_mode === 'systematic' ? 'Systematic SIP' : 'Manual'}</span>
                {s.funding_mode === 'systematic' && s.sip_amount && (
                    <span><strong>SIP:</strong> {s.sip_amount} ({s.sip_frequency})</span>
                )}
                </div>
                </div>
            ))}
            </div>
        )}
        </div>
    );
}
