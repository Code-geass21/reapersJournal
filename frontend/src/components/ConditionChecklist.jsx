import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function ConditionChecklist({ strategyId, onChecksChange }) {
    const [rules, setRules] = useState([]);
    const [checks, setChecks] = useState({});

    useEffect(() => {
        if (!strategyId) return;

        const fetchRules = async () => {
            try {
                const res = await api.get(`/strategies/${strategyId}/rules`);
                setRules(res.data);

                // Initialize default false state for new rules
                const initialChecks = {};
                res.data.forEach(r => initialChecks[r.id] = false);
                setChecks(initialChecks);
                onChecksChange(Object.keys(initialChecks).map(id => ({ rule_id: parseInt(id), passed: false })));
            } catch (err) {
                console.error("Failed to load rules", err);
            }
        };
        fetchRules();
    }, [strategyId]);

    const toggleCheck = (ruleId) => {
        const newChecks = { ...checks, [ruleId]: !checks[ruleId] };
        setChecks(newChecks);

        // Pass the updated array back up to the parent form
        onChecksChange(Object.keys(newChecks).map(id => ({
            rule_id: parseInt(id),
                                                         passed: newChecks[id]
        })));
    };

    if (rules.length === 0) return null;

    return (
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--border-color)', marginTop: '1rem' }}>
        <h4 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)' }}>Strategy Rules Checklist</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {rules.map(rule => (
            <label key={rule.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input
            type="checkbox"
            checked={checks[rule.id] || false}
            onChange={() => toggleCheck(rule.id)}
            style={{ width: '16px', height: '16px' }}
            />
            <span style={{
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                background: rule.rule_type === 'risk' ? '#ef444440' : rule.rule_type === 'entry' ? '#22c55e40' : '#3b82f640',
                color: rule.rule_type === 'risk' ? '#fca5a5' : rule.rule_type === 'entry' ? '#86efac' : '#93c5fd'
            }}>
            {rule.rule_type}
            </span>
            {rule.label} {rule.is_required && <span style={{ color: '#ef4444' }}>*</span>}
            </label>
        ))}
        </div>
        </div>
    );
}
