import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Inbox,
    ShieldAlert,
    PlusCircle,
    PlayCircle,
    FileBarChart
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import TransactionDetail from './pages/TransactionDetail';
import HITLQueue from './pages/HITLQueue';
import ManualEntry from './pages/ManualEntry';
import Simulator from './pages/Simulator';
import Reports from './pages/Reports';

function Sidebar() {
    const location = useLocation();

    const navItems = [
        { path: '/', name: 'Dashboard', icon: LayoutDashboard },
        { path: '/hitl', name: 'HITL Queue', icon: Inbox },
        { path: '/manual-entry', name: 'Manual Entry', icon: PlusCircle },
        { path: '/simulator', name: 'Simulator', icon: PlayCircle },
        { path: '/reports', name: 'Audit Reports', icon: FileBarChart },
    ];

    return (
        <div className="w-64 bg-bcp-blue text-white h-screen fixed left-0 top-0 flex flex-col">
            <div className="p-6 border-b border-white/10">
                <h1 className="text-xl font-bold flex items-center gap-2">
                    <ShieldAlert className="text-bcp-orange" />
                    Fraud Guard
                </h1>
            </div>
            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`flex items-center gap-3 p-3 rounded-xl transition-all ${location.pathname === item.path ? 'bg-white/10 text-bcp-orange' : 'hover:bg-white/5 text-gray-300'
                            }`}
                    >
                        <item.icon size={20} />
                        {item.name}
                    </Link>
                ))}
            </nav>
            <div className="p-4 border-t border-white/10 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-bcp-orange flex items-center justify-center font-bold">A</div>
                <div className="text-sm">
                    <p className="font-medium">Analista BCP</p>
                    <p className="text-gray-400 text-xs">Admin</p>
                </div>
            </div>
        </div>
    );
}

function App() {
    return (
        <div className="flex bg-gray-50 min-h-screen">
            <Sidebar />
            <main className="ml-64 flex-1 p-8">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/transaction/:id" element={<TransactionDetail />} />
                    <Route path="/hitl" element={<HITLQueue />} />
                    <Route path="/manual-entry" element={<ManualEntry />} />
                    <Route path="/simulator" element={<Simulator />} />
                    <Route path="/reports" element={<Reports />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;
