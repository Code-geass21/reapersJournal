import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function Settings() {
    const [activeTab, setActiveTab] = useState('data'); // 'data' or 'backup'
    const [instruments, setInstruments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloading, setDownloading] = useState(false);

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

    const handleCreateInstrument = async (e) => {
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

    const handleDownloadBackup = async () => {
        setDownloading(true);
        try {
            // Must use responseType blob for binary file downloads
            const res = await api.get('/backup/download', { responseType: 'blob' });

            // Create a hidden anchor tag to trigger the browser download
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;

            // Extract filename from headers if possible, otherwise use default
            const disposition = res.headers['content-disposition'];
            let filename = `reapers_journal_backup_${new Date().getTime()}.zip`;
            if (disposition && disposition.indexOf('filename=') !== -1) {
                filename = disposition.split('filename=')[1].replace(/['"]/g, '');
            }

            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (err) {
            alert('Backup failed to generate or download.');
            console.error(err);
        } finally {
            setDownloading(false);
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading Settings...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #334155', marginBottom: '2rem' }}>
        <button
        onClick={() => setActiveTab('data')}
        style={{ background: 'none', border: 'none', color: activeTab === 'data' ? '#22d3ee' : '#94a3b8', padding: '0.5rem 1rem', fontSize: '1rem', fontWeight: activeTab === 'data' ? 'bold' : 'normal', borderBottom: activeTab === 'data' ? '2px solid #22d3ee' : '2px solid transparent', cursor: 'pointer' }}
        >
        Instruments
        </button>
        <button
        onClick={() => setActiveTab('backup')}
        style={{ background: 'none', border: 'none', color: activeTab === 'backup' ? '#22d3ee' : '#94a3b8', padding: '0.5rem 1rem', fontSize: '1rem', fontWeight: activeTab === 'backup' ? 'bold' : 'normal', borderBottom: activeTab === 'backup' ? '2px solid #22d3ee' : '2px solid transparent', cursor: 'pointer' }}
        >
        Backup & Export
        </button>
        </div>

        {activeTab === 'data' && (
            <>
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h3 style={{ marginTop: 0 }}>Add Currency Pair</h3>
            <form onSubmit={handleCreateInstrument} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
            </>
        )}

        {activeTab === 'backup' && (
            <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '8px', borderLeft: '4px solid #3b82f6' }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>Data Portability</h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.5', marginBottom: '2rem' }}>
            Reaper's Journal is designed to keep you in full control of your data.
            Clicking the button below will generate a ZIP file containing every strategy, rule,
            trade, checklist, and transaction associated with your account in plain JSON format,
            along with the original image files for all of your trade screenshots.
            </p>
            <button
            onClick={handleDownloadBackup}
            disabled={downloading}
            style={{
                background: downloading ? '#334155' : '#3b82f6',
                color: '#f8fafc',
                padding: '1rem 2rem',
                fontWeight: 'bold',
                border: 'none',
                cursor: downloading ? 'not-allowed' : 'pointer',
                borderRadius: '4px',
                width: '100%',
                fontSize: '1.1rem'
            }}
            >
            {downloading ? 'Compiling Backup...' : '↓ Download Full Backup (.zip)'}
            </button>
            </div>
        )}
        </div>
    );
}
