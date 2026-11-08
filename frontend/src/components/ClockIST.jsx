import React, { useState, useEffect } from 'react';

export default function ClockIST() {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    // Format strictly for Asia/Kolkata
    const timeString = time.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-color)', padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold' }}>IST</span>
        <span style={{ color: 'var(--accent)', fontFamily: 'monospace', fontSize: '1.125rem' }}>{timeString}</span>
        </div>
    );
}
