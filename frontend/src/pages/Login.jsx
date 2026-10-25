import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, register } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            if (isRegister) {
                await register(username, email, password);
            } else {
                await login(username, password);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        }
    };

    return (
        <div style={{ maxWidth: '350px', margin: '100px auto', padding: '2rem', background: '#1e293b', borderRadius: '8px' }}>
        <h2 style={{ marginTop: 0 }}>{isRegister ? 'Create Admin' : 'Login'}</h2>
        {error && <p style={{ color: '#ef4444' }}>{error}</p>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        required
        style={{ padding: '0.5rem' }}
        />
        {isRegister && (
            <input
            placeholder="Email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={{ padding: '0.5rem' }}
            />
        )}
        <input
        placeholder="Password"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
        style={{ padding: '0.5rem' }}
        />
        <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer' }}>
        {isRegister ? 'Register' : 'Login'}
        </button>
        </form>

        <button
        onClick={() => setIsRegister(!isRegister)}
        style={{ background: 'none', color: '#22d3ee', border: 'none', marginTop: '1rem', cursor: 'pointer', width: '100%' }}
        >
        {isRegister ? 'Already have an account? Login' : 'Need an account? Register'}
        </button>
        </div>
    );
}
