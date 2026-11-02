import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function StrategyPicker({ selectedIds, onChange }) {
    const [strategies, setStrategies] = useState([]);

    useEffect(() => {
        api.get('/strategies/').then(res => setStrategies(res.data)).catch(console.error);
    }, []);

    const toggleStrategy = (id) => {
        if (selectedIds.includes(id)) {
            onChange(selectedIds.filter(sId => sId !== id));
        } else {
            onChange([...selectedIds, id]);
        }
    };

    return (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {strategies.map(s => (
            <button
            key={s.id}
            onClick={() => toggleStrategy(s.id)}
            type="button"
            style={{
                background: selectedIds.includes(s.id) ? '#22d3ee' : '#334155',
                              color: selectedIds.includes(s.id) ? '#0f172a' : '#f8fafc',
                              border: 'none', padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'
            }}
            >
            {s.name}
            </button>
        ))}
        </div>
    );
}
