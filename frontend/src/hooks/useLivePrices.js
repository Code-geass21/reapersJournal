import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useLivePrices(refreshIntervalSecs = 10) {
    const [liveData, setLiveData] = useState({}); // Keyed by trade_id
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;

        const fetchPrices = async () => {
            try {
                // Don't fetch if not logged in
                if (!localStorage.getItem('token')) return;

                const res = await api.get('/prices/open');
                if (isMounted) {
                    // Convert array to dictionary keyed by trade_id for O(1) lookup in UI
                    const dataDict = {};
                    res.data.forEach(item => {
                        dataDict[item.trade_id] = item;
                    });
                    setLiveData(dataDict);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    console.error("Failed to fetch live prices", err);
                    setError(err);
                }
            }
        };

        // Fetch immediately, then loop
        fetchPrices();
        const intervalId = setInterval(fetchPrices, refreshIntervalSecs * 1000);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [refreshIntervalSecs]);

    return { liveData, error };
}
