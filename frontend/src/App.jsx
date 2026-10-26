import { Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Strategies from './pages/Strategies';

function App() {
    const { token, logout } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <div>
        {/* Simple Top Navigation */}
        <nav style={{ background: '#1e293b', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#22d3ee' }}>Reaper's Journal</h1>
        <Link to="/" style={{ color: '#f8fafc', textDecoration: 'none' }}>Dashboard</Link>
        <Link to="/strategies" style={{ color: '#f8fafc', textDecoration: 'none' }}>Strategies</Link>
        </div>
        <button
        onClick={logout}
        style={{ background: 'none', color: '#94a3b8', border: '1px solid #94a3b8', padding: '0.25rem 1rem', cursor: 'pointer', borderRadius: '4px' }}
        >
        Logout
        </button>
        </nav>

        {/* Route Content */}
        <main>
        <Routes>
        <Route path="/" element={<div style={{ padding: '2rem' }}><h2>Dashboard Placeholder</h2><p>Welcome to Phase 1/2.</p></div>} />
        <Route path="/strategies" element={<Strategies />} />
        </Routes>
        </main>
        </div>
    )
}

export default App
