import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useTheme() {
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        const fetchTheme = async () => {
            try {
                if (localStorage.getItem('token')) {
                    const res = await api.get('/settings/preferences');
                    const userTheme = res.data.theme || 'dark';
                    setTheme(userTheme);
                    document.documentElement.setAttribute('data-theme', userTheme);
                }
            } catch (e) {
                console.error('Failed to load theme preference', e);
            }
        };
        fetchTheme();
    }, []);

    const toggleTheme = async () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
        try {
            await api.put('/settings/preferences', { theme: newTheme });
        } catch (e) {
            console.error('Failed to save theme', e);
        }
    };

    return { theme, toggleTheme };
}
