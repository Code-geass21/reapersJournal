import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';

export default function Strategies() {
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Form state
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [newStrategy, setNewStrategy] = useState({
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

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            // Clean up empty numbers
            const payload = { ...newStrategy };
            if (!payload.sip_amount) payload.sip_amount = null;

            await api.post('/strategies/', payload);
            setIsFormOpen(false);
            setNewStrategy({ name: '', description: '', market: 'FOREX', funding_mode: 'non_systematic', sip_amount: '', sip_frequency: 'monthly' });
            fetchStrategies(); // Refresh the list
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create strategy');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading strategies...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>My Strategies</h2>
        <button
        onClick={() => setIsFormOpen(!isFormOpen)}
        style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', border: 'none', fontWeight: 'bold', cursor: 'pointer', borderRadius: '4px' }}
        >
        {isFormOpen ? 'Cancel' : '+ New Strategy'}
        </button>
        </div>

        {error && <p style={{ color: '#ef4444' }}>{error}</p>}

        {isFormOpen && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <input
            placeholder="Strategy Name (e.g., London Breakout)"
            value={newStrategy.name}
            onChange={e => setNewStrategy({...newStrategy, name: e.target.value})}
            required
            style={{ padding: '0.5rem' }}
            />
            <textarea
            placeholder="Description"
            value={newStrategy.description}
            onChange={e => setNewStrategy({...newStrategy, description: e.target.value})}
            style={{ padding: '0.5rem', minHeight: '80px' }}
            />

            <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Market</label>
            <select
            value={newStrategy.market}
            onChange={e => setNewStrategy({...newStrategy, market: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            >
            <option value="FOREX">Forex</option>
            {/* Future markets will go here */}
            </select>
            </div>
            <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Funding Mode</label>
            <select
            value={newStrategy.funding_mode}
            onChange={e => setNewStrategy({...newStrategy, funding_mode: e.target.value})}
            style={{ width: '100%', padding: '0.5rem' }}
            >
            <option value="non_systematic">Non-Systematic (Manual)</option>
            <option value="systematic">Systematic (SIP/Recurring)</option>
            </select>
            </div>
            </div>

            {newStrategy.funding_mode === 'systematic' && (
                <div style={{ display: 'flex', gap: '1rem' }}>
                <input
                type="number"
                placeholder="SIP Amount"
                value={newStrategy.sip_amount}
                onChange={e => setNewStrategy({...newStrategy, sip_amount: e.target.value})}
                style={{ flex: 1, padding: '0.5rem' }}
                required
                />
                <select
                value={newStrategy.sip_frequency}
                onChange={e => setNewStrategy({...newStrategy, sip_frequency: e.target.value})}
                style={{ flex: 1, padding: '0.5rem' }}
                >
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                </select>
                </div>
            )}

            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', marginTop: '0.5rem', borderRadius: '4px' }}>
            Save Strategy
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
                {/* Make the name clickable */}
                <h3 style={{ margin: '0 0 0.5rem 0' }}>
                <Link to={`/strategies/${s.id}`} style={{ color: '#f8fafc', textDecoration: 'none' }}>
                {s.name} →
                </Link>
                </h3>
                {s.description && <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1' }}>{s.description}</p>}
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
