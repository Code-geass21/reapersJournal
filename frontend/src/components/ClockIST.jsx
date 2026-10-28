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
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#0f172a', padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #334155' }}>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>IST</span>
        <span style={{ color: '#22d3ee', fontFamily: 'monospace', fontSize: '1.125rem' }}>{timeString}</span>
        </div>
    );
}
