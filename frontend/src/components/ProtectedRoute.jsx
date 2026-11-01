import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function ProtectedRoute() {
    const { token } = useAuth();

    // If not authenticated, kick them back to login
    if (!token) {
        return <Navigate to="/" replace />;
    }

    // Otherwise, render the child route
    return <Outlet />;
}
