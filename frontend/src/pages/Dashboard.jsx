import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowRight, TrendingUp, AlertCircle, CheckCircle, ShieldAlert } from 'lucide-react';
import api from '../services/api';

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="glass-card p-6 rounded-2xl flex items-center gap-4">
        <div className={`p-3 rounded-xl ${color}`}>
            <Icon size={24} />
        </div>
        <div>
            <p className="text-gray-500 text-sm font-medium">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    </div>
);

function Dashboard() {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // In a real app we might have a list endpoint, using analyze/ for demo if needed 
        // or just fetching what we have from a generic /transactions/ endpoint if implemented
        api.get('/admin/core/transaction/').then(res => {
            // Mocking some data if the admin endpoint isn't public API
            // Since Step 9 might not have a full "list" endpoint, we use dummy data for UI demo
            setTransactions([
                { id: 'T-001', amount: 1500.00, decision: 'APPROVE', confidence: 0.98, timestamp: '2026-01-29 10:00' },
                { id: 'T-002', amount: 5000.00, decision: 'BLOCK', confidence: 0.92, timestamp: '2026-01-29 10:05' },
                { id: 'T-003', amount: 2500.00, decision: 'ESCALATE_TO_HUMAN', confidence: 0.65, timestamp: '2026-01-29 10:10' },
                { id: 'T-004', amount: 120.00, decision: 'APPROVE', confidence: 0.99, timestamp: '2026-01-29 10:15' },
            ]);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            // Fallback dummy data for demo
            setTransactions([
                { id: 'T-001', amount: 1500.00, decision: 'APPROVE', confidence: 0.98, timestamp: '2026-01-29 10:00' },
                { id: 'T-002', amount: 5000.00, decision: 'BLOCK', confidence: 0.92, timestamp: '2026-01-29 10:05' },
                { id: 'T-003', amount: 2500.00, decision: 'ESCALATE_TO_HUMAN', confidence: 0.65, timestamp: '2026-01-29 10:10' },
            ]);
            setLoading(false);
        });
    }, []);

    const getStatusColor = (decision) => {
        switch (decision) {
            case 'APPROVE': return 'status-approve';
            case 'BLOCK': return 'status-block';
            case 'CHALLENGE': return 'status-challenge';
            case 'ESCALATE_TO_HUMAN': return 'status-escalate';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900 leading-tight">Consola de Monitoreo</h2>
                    <p className="text-gray-500">Supervisión en tiempo real de transacciones sospechosas.</p>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Buscar transacción..."
                            className="pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-bcp-blue/20"
                        />
                    </div>
                    <button className="btn-secondary">
                        <Filter size={18} />
                        Filtros
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Analizadas" value="1,284" icon={TrendingUp} color="bg-blue-100 text-blue-600" />
                <StatCard title="Bloqueadas" value="42" icon={ShieldAlert} color="bg-red-100 text-red-600" />
                <StatCard title="Pendiente HITL" value="8" icon={AlertCircle} color="bg-orange-100 text-orange-600" />
                <StatCard title="Tasa de Precisión" value="99.2%" icon={CheckCircle} color="bg-green-100 text-green-600" />
            </div>

            <div className="glass-card rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-gray-100 bg-white/50">
                    <h3 className="font-bold text-lg">Transacciones Recientes</h3>
                </div>
                <table className="w-full text-left">
                    <thead className="bg-gray-50/50 text-gray-500 text-sm uppercase">
                        <tr>
                            <th className="px-6 py-4 font-semibold">ID Transacción</th>
                            <th className="px-6 py-4 font-semibold">Monto</th>
                            <th className="px-6 py-4 font-semibold">Decisión IA</th>
                            <th className="px-6 py-4 font-semibold">Confianza</th>
                            <th className="px-6 py-4 font-semibold">Fecha/Hora</th>
                            <th className="px-6 py-4 font-semibold text-right">Acción</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {transactions.map((tx) => (
                            <tr key={tx.id} className="hover:bg-gray-50/80 transition-colors">
                                <td className="px-6 py-4 font-medium text-gray-900">{tx.id}</td>
                                <td className="px-6 py-4">${tx.amount.toLocaleString()}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(tx.decision)}`}>
                                        {tx.decision}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-16 bg-gray-200 h-1.5 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${tx.confidence > 0.8 ? 'bg-green-500' : 'bg-orange-500'}`}
                                                style={{ width: `${tx.confidence * 100}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-sm font-medium">{(tx.confidence * 100).toFixed(0)}%</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-gray-500 text-sm">{tx.timestamp}</td>
                                <td className="px-6 py-4 text-right">
                                    <Link to={`/transaction/${tx.transaction_id || tx.id}`} className="text-bcp-blue hover:text-bcp-orange transition-colors">
                                        <ArrowRight size={20} />
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default Dashboard;
