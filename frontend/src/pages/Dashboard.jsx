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
    const [stats, setStats] = useState({
        total_analyzed: 0,
        blocked: 0,
        pending_hitl: 0,
        accuracy: 99.2
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, txRes] = await Promise.all([
                    api.get('dashboard/stats/'),
                    api.get('transactions/')
                ]);
                setStats(statsRes.data);
                setTransactions(txRes.data);
            } catch (err) {
                console.error("Error fetching dashboard data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        // Polling cada 30 segundos para actualizar el dashboard
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
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
                <StatCard title="Total Analizadas" value={stats.total_analyzed.toLocaleString()} icon={TrendingUp} color="bg-blue-100 text-blue-600" />
                <StatCard title="Bloqueadas" value={stats.blocked.toLocaleString()} icon={ShieldAlert} color="bg-red-100 text-red-600" />
                <StatCard title="Pendiente HITL" value={stats.pending_hitl.toLocaleString()} icon={AlertCircle} color="bg-orange-100 text-orange-600" />
                <StatCard title="Tasa de Precisión" value={`${stats.accuracy}%`} icon={CheckCircle} color="bg-green-100 text-green-600" />
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
