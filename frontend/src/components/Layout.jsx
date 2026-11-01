import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function Layout() {
    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-color, #0f172a)' }}>
        <Sidebar />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <TopBar />
        <main style={{ flex: 1, overflowY: 'auto' }}>
        {/* The current route's page will render inside this Outlet */}
        <Outlet />
        </main>
        </div>
        </div>
    );
}
