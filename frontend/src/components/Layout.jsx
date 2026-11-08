import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function Layout() {
    const [maintenanceMode, setMaintenanceMode] = useState(false);

    useEffect(() => {
        const handleMaintenance = () => setMaintenanceMode(true);
        window.addEventListener('maintenance-mode', handleMaintenance);
        return () => window.removeEventListener('maintenance-mode', handleMaintenance);
    }, []);

    return (
        <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
            <Sidebar />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {maintenanceMode && (
                    <div style={{ background: '#eab308', color: '#0f172a', padding: '0.5rem', textAlign: 'center', fontWeight: 'bold', fontSize: '14px', zIndex: 1000 }}>
                        ⚠️ System is currently in maintenance mode. Some features are disabled.
                    </div>
                )}
                <TopBar />
                <main style={{ flex: 1, overflowY: 'auto', backgroundColor: 'var(--bg-color)' }}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
