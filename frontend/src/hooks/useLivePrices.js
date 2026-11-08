import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

export function useLivePrices(refreshIntervalSecs = 3) {
    const [liveData, setLiveData] = useState({});
    const [error, setError] = useState(null);
    const [isMaintenance, setIsMaintenance] = useState(false);

    // Listen to global maintenance event dispatched by api.js interceptor
    useEffect(() => {
        const handleMaintenance = () => setIsMaintenance(true);
        window.addEventListener('maintenance-mode', handleMaintenance);
        return () => window.removeEventListener('maintenance-mode', handleMaintenance);
    }, []);

    const fetchPrices = useCallback(async () => {
        if (isMaintenance) return;
        try {
            if (!localStorage.getItem('token')) return;

            const res = await api.get('/prices/open');
            const dataDict = {};
            res.data.forEach(item => {
                dataDict[item.trade_id] = item;
            });
            setLiveData(dataDict);
            setError(null);
        } catch (err) {
            console.error("Failed to fetch live prices", err);
            setError(err);
            if (err.response && err.response.status === 503) {
                setIsMaintenance(true);
            }
        }
    }, [isMaintenance]);

    useEffect(() => {
        let isMounted = true;

        if (!isMaintenance) fetchPrices();

        const intervalId = setInterval(() => {
            if (isMounted && !isMaintenance) fetchPrices();
        }, refreshIntervalSecs * 1000);

            return () => {
                isMounted = false;
                clearInterval(intervalId);
            };
    }, [fetchPrices, refreshIntervalSecs, isMaintenance]);

    return { liveData, error, forceRefresh: fetchPrices };
}
