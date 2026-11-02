import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useDefaultStrategies() {
    const [defaultIds, setDefaultIds] = useState([]);

    useEffect(() => {
        api.get('/settings/preferences')
        .then(res => setDefaultIds(res.data.default_strategy_ids || []))
        .catch(console.error);
    }, []);

    return { defaultIds, setDefaultIds };
}
