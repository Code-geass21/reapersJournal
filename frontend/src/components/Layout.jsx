import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function Layout() {
    const [maintenanceMode, setMaintenanceMode] = useState(false);

    useEffect(() => {
        const handleMaintenance = () => setMaintenanceMode(true);
        const handleRecover = () => setMaintenanceMode(false);

        window.addEventListener('maintenance-mode', handleMaintenance);
        window.addEventListener('maintenance-recovered', handleRecover);

        return () => {
            window.removeEventListener('maintenance-mode', handleMaintenance);
            window.removeEventListener('maintenance-recovered', handleRecover);
        };
    }, []);

    return (
        <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
            <Sidebar />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {maintenanceMode && (
                    <div style={{ background: '#eab308', color: 'var(--bg-color)', padding: '0.5rem', textAlign: 'center', fontWeight: 'bold', fontSize: '14px', zIndex: 1000 }}>
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
