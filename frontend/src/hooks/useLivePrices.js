import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

export function useLivePrices(refreshIntervalSecs = 3) {
    const [liveData, setLiveData] = useState({});
    const [error, setError] = useState(null);
    const [isMaintenance, setIsMaintenance] = useState(false);

    useEffect(() => {
        const handleMaintenance = () => setIsMaintenance(true);
        const handleRecovered = () => setIsMaintenance(false);
        window.addEventListener('maintenance-mode', handleMaintenance);
        window.addEventListener('maintenance-recovered', handleRecovered);
        return () => {
            window.removeEventListener('maintenance-mode', handleMaintenance);
            window.removeEventListener('maintenance-recovered', handleRecovered);
        };
    }, []);

    const fetchPrices = useCallback(async () => {
        // REMOVED the strict `if (isMaintenance) return;` block so it can attempt a recovery poll
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
    }, []);

    useEffect(() => {
        let isMounted = true;
        fetchPrices();

        // FIX FOR BUG 76: Back-off polling to 30s during maintenance to avoid spamming the offline backend
        const currentInterval = isMaintenance ? 30000 : refreshIntervalSecs * 1000;

        const intervalId = setInterval(() => {
            if (isMounted) fetchPrices();
        }, currentInterval);

            return () => {
                isMounted = false;
                clearInterval(intervalId);
            };
    }, [fetchPrices, refreshIntervalSecs, isMaintenance]);

    return { liveData, error, forceRefresh: fetchPrices };
}
