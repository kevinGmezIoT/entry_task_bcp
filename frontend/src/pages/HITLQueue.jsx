import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCheck, MessageCircle, Send, ShieldAlert, Check, X, Info } from 'lucide-react';
import api from '../services/api';

function HITLQueue() {
    const [cases, setCases] = useState([]);
    const [selectedCase, setSelectedCase] = useState(null);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchCases();
    }, []);

    const fetchCases = () => {
        api.get('/hitl/cases/').then(res => {
            setCases(res.data);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            // Dummy data
            setCases([
                { id: 1, transaction: { transaction_id: 'T-003', amount: 2500, customer: { customer_id: 'C-123' } }, status: 'OPEN', created_at: '2026-01-29 10:10' }
            ]);
            setLoading(false);
        });
    };

    const resolveCase = (decision) => {
        if (!selectedCase) return;
        api.post(`/hitl/cases/${selectedCase.id}/resolve/`, { decision, notes })
            .then(() => {
                setSelectedCase(null);
                setNotes('');
                fetchCases();
            }).catch(alert);
    };

    if (loading) return <div>Cargando...</div>;

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold text-gray-900">Cola de Revisión Humana (HITL)</h2>
                <p className="text-gray-500">Decisiones de baja confianza escaladas para análisis experto.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* List side */}
                <div className="lg:col-span-1 space-y-4">
                    <h3 className="font-bold flex items-center gap-2 text-gray-600 uppercase text-xs">
                        <ShieldAlert size={14} /> Casos Pendientes ({cases.length})
                    </h3>
                    {cases.length === 0 ? (
                        <div className="bg-white p-8 rounded-2xl text-center text-gray-400 border border-dashed border-gray-200">
                            No hay casos pendientes.
                        </div>
                    ) : (
                        cases.map(c => (
                            <div
                                key={c.id}
                                onClick={() => setSelectedCase(c)}
                                className={`p-4 rounded-2xl cursor-pointer transition-all border ${selectedCase?.id === c.id ? 'bg-bcp-blue text-white ring-4 ring-bcp-blue/10' : 'bg-white hover:border-bcp-blue/30'
                                    }`}
                            >
                                <div className="flex justify-between items-start">
                                    <span className="font-bold">{c.transaction.transaction_id}</span>
                                    <span className="text-xs opacity-70">{new Date(c.created_at).toLocaleTimeString()}</span>
                                </div>
                                <p className={`text-sm ${selectedCase?.id === c.id ? 'text-blue-100' : 'text-gray-500'}`}>
                                    Monto: {c.transaction.amount} {c.transaction.currency || 'USD'} • Cliente: {c.transaction.customer.customer_id}
                                </p>
                            </div>
                        ))
                    )}
                </div>

                {/* Action side */}
                <div className="lg:col-span-2">
                    {selectedCase ? (
                        <div className="glass-card rounded-2xl p-8 space-y-8">
                            <div className="flex justify-between items-start">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                                        <UserCheck size={24} />
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold">Analizando {selectedCase.transaction.transaction_id}</h4>
                                        <p className="text-gray-500 text-sm">Escalado por: Arbiter Agent (Confianza 65%)</p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button className="p-2 bg-gray-100 text-gray-600 rounded-lg" title="Ver detalles de auditoría full">
                                        <Info size={18} />
                                    </button>
                                </div>
                            </div>

                            <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100">
                                <h5 className="text-xs font-bold text-gray-400 uppercase mb-4 flex items-center gap-2">
                                    <MessageCircle size={14} /> Notas del Analista
                                </h5>
                                <textarea
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    placeholder="Escribe el motivo de tu decisión..."
                                    className="w-full bg-transparent border-none focus:ring-0 text-gray-700 resize-none h-32"
                                />
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <button onClick={() => resolveCase('APPROVE')} className="p-4 bg-green-50 text-green-700 rounded-2xl border border-green-100 hover:bg-green-100 transition-all flex flex-col items-center gap-2">
                                    <Check size={24} />
                                    <span className="font-bold">Aprobar</span>
                                </button>
                                <button onClick={() => resolveCase('CHALLENGE')} className="p-4 bg-orange-50 text-orange-700 rounded-2xl border border-orange-100 hover:bg-orange-100 transition-all flex flex-col items-center gap-2">
                                    <ShieldAlert size={24} />
                                    <span className="font-bold">Challenge</span>
                                </button>
                                <button onClick={() => resolveCase('BLOCK')} className="p-4 bg-red-50 text-red-700 rounded-2xl border border-red-100 hover:bg-red-100 transition-all flex flex-col items-center gap-2">
                                    <X size={24} />
                                    <span className="font-bold">Bloquear</span>
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="glass-card rounded-2xl p-12 text-center text-gray-400 space-y-4">
                            <div className="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center mx-auto text-gray-300">
                                <ShieldAlert size={32} />
                            </div>
                            <p>Selecciona un caso de la izquierda para comenzar la revisión experta.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default HITLQueue;
