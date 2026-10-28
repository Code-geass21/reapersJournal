import { Routes, Route } from 'react-router-dom';
import { useAuth } from './hooks/useAuth'

// Pages
import Login from './pages/Login'
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Journal from './pages/Journal';
import TradeDetail from './pages/TradeDetail';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';

// Components
import TopBar from './components/TopBar';

function App() {
    const { token } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <div>
        {/* The new persistent TopBar replaces the hardcoded nav */}
        <TopBar />

        <main>
        <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/journal/:id" element={<TradeDetail />} />
        <Route path="/strategies" element={<Strategies />} />
        <Route path="/strategies/:id" element={<StrategyDetail />} />
        <Route path="/settings" element={<Settings />} />
        </Routes>
        </main>
        </div>
    )
}
export default App
