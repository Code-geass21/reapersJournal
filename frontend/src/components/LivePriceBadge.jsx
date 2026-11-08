import React from 'react';

export default function LivePriceBadge({ liveData, isLong }) {
    if (!liveData) {
        return (
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'var(--border-color)', color: 'var(--text-muted)' }}>
            Fetching...
            </span>
        );
    }

    const { current_price, unrealized_pnl, is_stale, stale_threshold_secs } = liveData;

    // FIX FOR BUG 82: Handle null P&L cleanly
    const hasPnl = unrealized_pnl !== null && unrealized_pnl !== undefined;
    const isProfitable = hasPnl && unrealized_pnl >= 0;

    const color = hasPnl ? (isProfitable ? '#22c55e' : '#ef4444') : 'var(--text-muted)';
    const bgColor = hasPnl ? (isProfitable ? '#22c55e20' : '#ef444420') : 'var(--border-color)';

    const formatStaleness = (secs) => {
        if (!secs) return "Data is stale";
        if (secs < 60) return `${secs} seconds`;
        if (secs < 3600) return `${Math.floor(secs / 60)} minutes`;
        return `${Math.floor(secs / 3600)} hours`;
    };

    return (
        <span
        title={is_stale ? `Data is older than ${formatStaleness(stale_threshold_secs)}` : "Live Price"}
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
        ({hasPnl ? `${isProfitable ? '+' : ''}${unrealized_pnl.toFixed(2)}` : 'N/A'})
        </span>
        {is_stale && ' ⚠️'}
        </span>
    );
}
