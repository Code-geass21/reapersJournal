import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function StrategyPicker({ value, onChange, multi = false }) {
    const [strategies, setStrategies] = useState([]);

    useEffect(() => {
        const fetchStrategies = async () => {
            try {
                const res = await api.get('/strategies/');
                setStrategies(res.data);
            } catch (err) {
                console.error("Failed to load strategies for picker", err);
            }
        };
        fetchStrategies();
    }, []);

    return (
        <div>
        <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>
        {multi ? 'Filter by Strategies' : 'Select Strategy'}
        </label>
        <select
        multiple={multi}
        value={value}
        onChange={(e) => {
            if (multi) {
                const selected = Array.from(e.target.selectedOptions, option => option.value);
                onChange(selected);
            } else {
                onChange(e.target.value);
            }
        }}
        style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', borderRadius: '4px', minHeight: multi ? '80px' : 'auto' }}
        required={!multi}
        >
        {!multi && <option value="">-- Select --</option>}
        {strategies.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
        ))}
        </select>
        </div>
    );
}
