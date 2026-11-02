import { Routes, Route } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import StrategyDetail from './pages/StrategyDetail';
import Journal from './pages/Journal';
import TradeDetail from './pages/TradeDetail';
import TradeForm from './pages/TradeForm';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import Help from './pages/Help';

// Components
import Layout from './components/Layout';

function App() {
    const { token } = useAuth();

    if (!token) {
        return <Login />;
    }

    return (
        <Routes>
        {/* Wrap all authenticated pages within the Layout */}
        <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/journal/new" element={<TradeForm />} />
        <Route path="/journal/:id" element={<TradeDetail />} />
        <Route path="/journal/:id/edit" element={<TradeForm />} />
        <Route path="/strategies" element={<Strategies />} />
        <Route path="/strategies/:id" element={<StrategyDetail />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/help" element={<Help />} />
        </Route>
        </Routes>
    );
}

export default App;
