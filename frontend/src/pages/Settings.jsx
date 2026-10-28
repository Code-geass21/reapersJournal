import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function Settings() {
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [newInst, setNewInst] = useState({
        symbol: '',
        provider_symbol: '',
        market_code: 'FOREX',
        pip_size: '0.0001',
        contract_size: 100000,
        quote_ccy: 'USD'
    });

    const fetchInstruments = async () => {
        try {
            const res = await api.get('/instruments/');
            setInstruments(res.data);
        } catch (err) {
            setError('Failed to load instruments.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInstruments();
    }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...newInst,
                pip_size: parseFloat(newInst.pip_size),
                contract_size: parseInt(newInst.contract_size)
            };
            await api.post('/instruments/', payload);
            setNewInst({ symbol: '', provider_symbol: '', market_code: 'FOREX', pip_size: '0.0001', contract_size: 100000, quote_ccy: 'USD' });
            fetchInstruments();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to add instrument');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading Settings...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ color: '#f8fafc', marginBottom: '2rem' }}>Data Management</h2>

        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0 }}>Add Currency Pair</h3>
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Display Symbol (e.g., AUD/JPY)</label>
        <input value={newInst.symbol} onChange={e => setNewInst({...newInst, symbol: e.target.value.toUpperCase()})} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>API Symbol (e.g., AUDJPY)</label>
        <input value={newInst.provider_symbol} onChange={e => setNewInst({...newInst, provider_symbol: e.target.value.toUpperCase()})} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Quote Currency (e.g., JPY)</label>
        <input value={newInst.quote_ccy} onChange={e => setNewInst({...newInst, quote_ccy: e.target.value.toUpperCase()})} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Pip Size (0.01 for JPY, 0.0001 for others)</label>
        <input type="number" step="any" value={newInst.pip_size} onChange={e => setNewInst({...newInst, pip_size: e.target.value})} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        </div>

        <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.75rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px', marginTop: '0.5rem' }}>
        + Add Instrument
        </button>
        </form>
        </div>

        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px' }}>
        <h3 style={{ marginTop: 0 }}>Active Instruments</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '1rem' }}>
        {instruments.map(inst => (
            <div key={inst.id} style={{ background: '#0f172a', padding: '1rem', borderRadius: '4px', textAlign: 'center', border: '1px solid #334155' }}>
            <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>{inst.symbol}</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Pip: {inst.pip_size}</div>
            </div>
        ))}
        </div>
        </div>
        </div>
    );
}
