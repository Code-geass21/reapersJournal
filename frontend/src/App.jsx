import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'

function App() {
    const { token, logout } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <div className="container">
        <h1>Reaper's Journal</h1>
        <p>Welcome! You are logged in.</p>
        <button
        onClick={logout}
        style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem 1rem', border: 'none', fontWeight: 'bold', cursor: 'pointer' }}
        >
        Logout
        </button>
        </div>
    )
}

export default App
