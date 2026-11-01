import React from 'react';

export default function MarketPicker({ value, onChange }) {
    return (
        <div>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>
        Market (Forex Only)
        </label>
        <select
        value={value || 'FOREX'}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', cursor: 'not-allowed' }}
        disabled
        >
        <option value="FOREX">Foreign Exchange (Forex)</option>
        </select>
        <span style={{ fontSize: '0.75rem', color: '#3b82f6' }}>Other markets planned for future updates.</span>
        </div>
    );
}
