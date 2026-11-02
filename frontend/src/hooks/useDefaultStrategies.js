import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useDefaultStrategies() {
    const [defaultStrategies, setDefaultStrategies] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDefaults = async () => {
            try {
                if (!localStorage.getItem('token')) return;
                const res = await api.get('/settings/preferences');
                setDefaultStrategies(res.data.default_strategy_ids || []);
            } catch (err) {
                console.error("Failed to load default strategies", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDefaults();
    }, []);

    return { defaultStrategies, loading };
}
