import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

export function useLivePrices(refreshIntervalSecs = 3) {
    const [liveData, setLiveData] = useState({});
    const [error, setError] = useState(null);

    const fetchPrices = useCallback(async () => {
        try {
            if (!localStorage.getItem('token')) return;

            // This only hits the local Postgres cache, so fast polling is virtually free
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
        }
    }, []);

    useEffect(() => {
        let isMounted = true;

        // Fetch instantly on mount
        fetchPrices();

        // Setup aggressive local polling loop
        const intervalId = setInterval(() => {
            if (isMounted) fetchPrices();
        }, refreshIntervalSecs * 1000);

            return () => {
                isMounted = false;
                clearInterval(intervalId);
            };
    }, [fetchPrices, refreshIntervalSecs]);

    return { liveData, error, forceRefresh: fetchPrices };
}
