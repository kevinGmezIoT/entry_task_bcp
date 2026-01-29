import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, User, DollarSign, Globe, MapPin, Smartphone, ShieldCheck } from 'lucide-react';
import api from '../services/api';

function ManualEntry() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        transaction_id: '',
        customer_id: 'C-1001',
        amount: 50.00,
        currency: 'PEN',
        country: 'PE',
        channel: 'WEB',
        device_id: 'DEV-99',
        merchant_id: 'M-500',
        timestamp: new Date().toISOString().slice(0, 16)
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await api.post('/transactions/create/', formData);
            navigate(`/transaction/${res.data.transaction_id || res.data.transaction}`);
        } catch (err) {
            console.error(err);
            alert('Error enviando transacción: ' + (err.response?.data?.error || err.message));
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div>
                <h2 className="text-3xl font-bold text-gray-900">Entrada Manual</h2>
                <p className="text-gray-500">Registra una transacción para evaluarla en tiempo real con el sistema multi-agente.</p>
            </div>

            <form onSubmit={handleSubmit} className="glass-card p-8 rounded-2xl space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            ID Transacción (Opcional)
                        </label>
                        <input
                            name="transaction_id"
                            placeholder="Autogenerado si está vacío"
                            value={formData.transaction_id}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            <User size={14} /> ID Cliente
                        </label>
                        <input
                            name="customer_id"
                            value={formData.customer_id}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            <DollarSign size={14} /> Monto
                        </label>
                        <div className="flex gap-2">
                            <select
                                name="currency"
                                value={formData.currency}
                                onChange={handleChange}
                                className="px-2 py-3 rounded-xl border border-gray-200 outline-none bg-gray-50"
                            >
                                <option value="PEN">PEN</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                            </select>
                            <input
                                type="number"
                                name="amount"
                                value={formData.amount}
                                onChange={handleChange}
                                className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            <Globe size={14} /> País
                        </label>
                        <select
                            name="country"
                            value={formData.country}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                        >
                            <option value="PE">Perú</option>
                            <option value="US">USA</option>
                            <option value="ES">España</option>
                            <option value="CO">Colombia</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            <Smartphone size={14} /> Canal
                        </label>
                        <select
                            name="channel"
                            value={formData.channel}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                        >
                            <option value="WEB">Web</option>
                            <option value="MOBILE">App Móvil</option>
                            <option value="POS">POS Físico</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            <Smartphone size={14} /> ID Dispositivo
                        </label>
                        <input
                            name="device_id"
                            value={formData.device_id}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            ID Comercio
                        </label>
                        <input
                            name="merchant_id"
                            value={formData.merchant_id}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                            Fecha/Hora
                        </label>
                        <input
                            type="datetime-local"
                            name="timestamp"
                            value={formData.timestamp}
                            onChange={handleChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-bcp-blue/20 outline-none"
                            required
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary justify-center py-4 text-lg"
                >
                    {loading ? (
                        <span className="flex items-center gap-2 italic">Analizando con Agentes...</span>
                    ) : (
                        <>
                            <ShieldCheck size={20} /> Evaluar Riesgo
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}

export default ManualEntry;
