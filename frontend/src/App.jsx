import { Routes, Route } from 'react-router-dom';
import { useAuth } from './hooks/useAuth'

// Components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login'
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Journal from './pages/Journal';
import TradeForm from './pages/TradeForm';
import TradeDetail from './pages/TradeDetail';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import Help from './pages/Help';

function App() {
    const { token } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <Routes>
        <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/journal" element={<Journal />} />
        {/* The new creation route must go before the ID route */}
        <Route path="/journal/new" element={<TradeForm />} />
        <Route path="/journal/:id" element={<TradeDetail />} />
        <Route path="/strategies" element={<Strategies />} />
        <Route path="/strategies/:id" element={<StrategyDetail />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/help" element={<Help />} />
        </Route>
        </Route>
        </Routes>
    )
}
export default App
