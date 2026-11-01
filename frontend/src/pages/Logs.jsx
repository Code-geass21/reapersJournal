import { useState, useEffect } from 'react';
import api from '../utils/api';
import { useAuth } from '../hooks/useAuth';

export default function Logs() {
    const { token } = useAuth();
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Filters
    const [levelFilter, setLevelFilter] = useState('');
    const [entityFilter, setEntityFilter] = useState('');
    const [expandedLog, setExpandedLog] = useState(null); // Tracks which row is clicked to show JSON diffs

    const fetchLogs = async () => {
        setLoading(true);
        try {
            let url = '/logs/?limit=200';
            if (levelFilter) url += `&level=${levelFilter}`;
            if (entityFilter) url += `&entity_type=${entityFilter}`;

            const res = await api.get(url);
            setLogs(res.data);
            setError('');
        } catch (err) {
            setError('Failed to load system logs.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [levelFilter, entityFilter]);

    const getLevelColor = (level) => {
        switch(level.toUpperCase()) {
            case 'ERROR': return { bg: '#ef444420', text: '#ef4444' };
            case 'WARNING': return { bg: '#eab30820', text: '#eab308' };
            default: return { bg: '#22d3ee20', text: '#22d3ee' };
        }
    };

    const toggleExpand = (id) => {
        setExpandedLog(expandedLog === id ? null : id);
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, color: '#f8fafc' }}>System Audit Logs</h2>
        <button
        onClick={fetchLogs}
        style={{ background: '#334155', color: '#f8fafc', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
        ↻ Refresh
        </button>
        </div>

        {/* Filter Bar */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', background: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Log Level</label>
        <select
        value={levelFilter}
        onChange={(e) => setLevelFilter(e.target.value)}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }}
        >
        <option value="">All Levels</option>
        <option value="INFO">INFO</option>
        <option value="WARNING">WARNING</option>
        <option value="ERROR">ERROR</option>
        </select>
        </div>
        <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Entity Type</label>
        <select
        value={entityFilter}
        onChange={(e) => setEntityFilter(e.target.value)}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px' }}
        >
        <option value="">All Entities</option>
        <option value="user">Users</option>
        <option value="trade">Trades</option>
        <option value="strategy">Strategies</option>
        <option value="system">System / Worker</option>
        </select>
        </div>
        </div>

        {error && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

        {/* Data Table */}
        <div style={{ background: '#1e293b', borderRadius: '8px', overflow: 'hidden' }}>
        {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading logs...</div>
        ) : logs.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No logs match your filters.</div>
        ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
            <tr style={{ background: '#0f172a', borderBottom: '1px solid #334155' }}>
            <th style={{ padding: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>Timestamp</th>
            <th style={{ padding: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>Level</th>
            <th style={{ padding: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>Action</th>
            <th style={{ padding: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>Entity</th>
            <th style={{ padding: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>Source</th>
            </tr>
            </thead>
            <tbody>
            {logs.map((log) => {
                const colors = getLevelColor(log.level);
                const isExpanded = expandedLog === log.id;

                return (
                    <React.Fragment key={log.id}>
                    {/* Main Row */}
                    <tr
                    onClick={() => toggleExpand(log.id)}
                    style={{
                        borderBottom: '1px solid #334155',
                        cursor: 'pointer',
                        background: isExpanded ? '#33415540' : 'transparent'
                    }}
                    >
                    <td style={{ padding: '1rem', color: '#cbd5e1' }}>
                    {new Date(log.ts).toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem' }}>
                    <span style={{
                        background: colors.bg, color: colors.text,
                        padding: '0.2rem 0.5rem', borderRadius: '4px',
                        fontSize: '0.75rem', fontWeight: 'bold'
                    }}>
                    {log.level}
                    </span>
                    </td>
                    <td style={{ padding: '1rem', color: '#f8fafc' }}>{log.action}</td>
                    <td style={{ padding: '1rem', color: '#94a3b8' }}>
                    {log.entity_type || '—'} {log.entity_id ? `#${log.entity_id}` : ''}
                    </td>
                    <td style={{ padding: '1rem', color: '#94a3b8' }}>{log.source}</td>
                    </tr>

                    {/* Expanded Payload Row */}
                    {isExpanded && (
                        <tr style={{ borderBottom: '1px solid #334155', background: '#0f172a' }}>
                        <td colSpan="5" style={{ padding: '1.5rem' }}>
                        <div style={{ display: 'flex', gap: '2rem' }}>
                        {log.before && (
                            <div style={{ flex: 1 }}>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#ef4444', fontSize: '0.875rem' }}>Before</h4>
                            <pre style={{ margin: 0, padding: '1rem', background: '#1e293b', borderRadius: '4px', color: '#cbd5e1', overflowX: 'auto' }}>
                            {JSON.stringify(log.before, null, 2)}
                            </pre>
                            </div>
                        )}

                        {log.after && (
                            <div style={{ flex: 1 }}>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#22c55e', fontSize: '0.875rem' }}>After</h4>
                            <pre style={{ margin: 0, padding: '1rem', background: '#1e293b', borderRadius: '4px', color: '#cbd5e1', overflowX: 'auto' }}>
                            {JSON.stringify(log.after, null, 2)}
                            </pre>
                            </div>
                        )}

                        {log.error_text && (
                            <div style={{ flex: 1 }}>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#ef4444', fontSize: '0.875rem' }}>Error Details</h4>
                            <pre style={{ margin: 0, padding: '1rem', background: '#ef444420', color: '#ef4444', borderRadius: '4px', overflowX: 'auto' }}>
                            {log.error_text}
                            </pre>
                            </div>
                        )}

                        {!log.before && !log.after && !log.error_text && (
                            <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>No detailed payload for this event.</span>
                        )}
                        </div>
                        </td>
                        </tr>
                    )}
                    </React.Fragment>
                );
            })}
            </tbody>
            </table>
        )}
        </div>
        </div>
    );
}
