import React from 'react';

export default function MarketPicker({ value, onChange }) {
    return (
        <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' }}
        >
        <option value="FOREX">Forex</option>
        <option value="IN_EQUITY" disabled>Indian Equity (Phase 2)</option>
        <option value="IN_FUTURES" disabled>Indian Futures (Phase 2)</option>
        <option value="IN_OPTIONS" disabled>Indian Options (Phase 2)</option>
        <option value="CRYPTO" disabled>Crypto (Future)</option>
        </select>
    );
}
