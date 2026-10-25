import { useState, createContext, useContext } from 'react';
import api from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(localStorage.getItem('token'));

    const login = async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await api.post('/auth/login', formData);
        setToken(res.data.access_token);
        localStorage.setItem('token', res.data.access_token);
    };

    const register = async (username, email, password) => {
        await api.post('/auth/register', { username, email, password });
        await login(username, password); // Auto-login after registration
    };

    const logout = () => {
        setToken(null);
        localStorage.removeItem('token');
    };

    return (
        <AuthContext.Provider value={{ token, login, register, logout }}>
        {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
