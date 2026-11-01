import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useTheme() {
    const [theme, setTheme] = useState('dark'); // Default to dark

    useEffect(() => {
        const fetchTheme = async () => {
            try {
                if (!localStorage.getItem('token')) return;
                const res = await api.get('/settings/preferences');
                const userTheme = res.data.theme || 'dark';
                setTheme(userTheme);
                document.documentElement.setAttribute('data-theme', userTheme);
            } catch (err) {
                console.error("Failed to fetch user theme preference", err);
            }
        };
        fetchTheme();
    }, []);

    const toggleTheme = async () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);

        try {
            // Persist to database
            await api.put('/settings/preferences', { theme: newTheme });
        } catch (err) {
            console.error("Failed to save theme to backend", err);
        }
    };

    return { theme, toggleTheme };
}
