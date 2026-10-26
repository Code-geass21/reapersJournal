import { Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Journal from './pages/Journal'; // <-- Import
import TradeDetail from './pages/TradeDetail';

function App() {
    const { token, logout } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <div>
        <nav style={{ background: '#1e293b', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#22d3ee' }}>Reaper's Journal</h1>
        <Link to="/" style={{ color: '#f8fafc', textDecoration: 'none' }}>Dashboard</Link>
        <Link to="/journal" style={{ color: '#f8fafc', textDecoration: 'none' }}>Journal</Link> {/* <-- Add Nav Link */}
        <Link to="/strategies" style={{ color: '#f8fafc', textDecoration: 'none' }}>Strategies</Link>
        </div>
        <button onClick={logout} style={{ background: 'none', color: '#94a3b8', border: '1px solid #94a3b8', padding: '0.25rem 1rem', cursor: 'pointer', borderRadius: '4px' }}>
        Logout
        </button>
        </nav>

        <main>
        <Routes>
        <Route path="/" element={<div style={{ padding: '2rem' }}><h2>Dashboard Placeholder</h2></div>} />
        <Route path="/journal" element={<Journal />} /> {/* <-- Add Route */}
        <Route path="/strategies" element={<Strategies />} />
        <Route path="/strategies/:id" element={<StrategyDetail />} />
        <Route path="/journal/:id" element={<TradeDetail />} />
        </Routes>
        </main>
        </div>
    )
}
export default App
