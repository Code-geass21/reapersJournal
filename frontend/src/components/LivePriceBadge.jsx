import React from 'react';

export default function LivePriceBadge({ liveData, isLong }) {
    if (!liveData) {
        return (
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: '#334155', color: '#94a3b8' }}>
            Fetching...
            </span>
        );
    }

    const { current_price, unrealized_pnl, unrealized_pips, is_stale } = liveData;

    // Determine color based on P&L
    const isProfitable = unrealized_pnl >= 0;
    const color = isProfitable ? '#22c55e' : '#ef4444';
    const bgColor = isProfitable ? '#22c55e20' : '#ef444420';

    return (
        <span
        title={is_stale ? "Data is older than 3 hours" : "Live Price"}
        style={{
            fontSize: '0.75rem',
            padding: '0.2rem 0.5rem',
            borderRadius: '4px',
            background: bgColor,
            color: color,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            border: is_stale ? '1px dashed #ef4444' : 'none'
        }}
        >
        {current_price.toFixed(5)}
        <span style={{ opacity: 0.7 }}>
        ({isProfitable ? '+' : ''}{unrealized_pnl.toFixed(2)})
        </span>
        {is_stale && ' ⚠️'}
        </span>
    );
}
