import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function NewsPanel() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchNews = async () => {
            try {
                const res = await api.get('/dashboard/news');
                setEvents(res.data.events || []);
            } catch (err) {
                setError('Failed to load calendar events.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchNews();
    }, []);

    if (loading) return <div style={{ color: '#94a3b8' }}>Loading Calendar...</div>;
    if (error) return <div style={{ color: '#ef4444' }}>{error}</div>;

    return (
        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', flex: 1, minWidth: '300px' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '1.2rem' }}>📅</span> Upcoming Volatility
        </h3>

        {events.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No major economic events in the next 48 hours.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {events.map((e, idx) => {
                const eventDate = new Date(e.time);
                const isHigh = e.impact === 'High';

                return (
                    <div key={idx} style={{ display: 'flex', gap: '1rem', alignItems: 'center', borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                    {/* Impact Badge */}
                    <div style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        background: isHigh ? '#ef444420' : '#f59e0b20',
                        color: isHigh ? '#ef4444' : '#f59e0b',
                        minWidth: '55px',
                        textAlign: 'center'
                    }}>
                    {e.impact.toUpperCase()}
                    </div>

                    {/* Event Details */}
                    <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>
                    {e.country} - {e.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {eventDate.toLocaleString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </div>
                    </div>
                    </div>
                )
            })}
            </div>
        )}
        </div>
    );
}
