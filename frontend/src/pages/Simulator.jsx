import React, { useState } from 'react';
import { Play, Database, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

function Simulator() {
    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const [message, setMessage] = useState('');

    const runSimulation = async () => {
        setStatus('loading');
        setMessage('Ejecutando seed_data en el servidor...');
        try {
            const res = await api.post('/transactions/seed/');
            setStatus('success');
            setMessage(res.data.status || 'Simulación completada con éxito.');
        } catch (err) {
            console.error(err);
            setStatus('error');
            setMessage('Error en la simulación: ' + (err.response?.data?.error || err.message));
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-4">
                <div className="w-20 h-20 bg-blue-100 text-bcp-blue rounded-full flex items-center justify-center mx-auto">
                    <Database size={40} />
                </div>
                <h2 className="text-4xl font-bold text-gray-900">Simulador de Datos</h2>
                <p className="text-gray-500 max-w-xl mx-auto">
                    Genera un lote de transacciones sintéticas, perfiles de clientes y políticas de fraude
                    basadas en los archivos locales para probar el sistema de detección masivo.
                </p>
            </div>

            <div className="glass-card p-12 rounded-3xl text-center space-y-8">
                {status === 'idle' && (
                    <>
                        <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 text-blue-800 text-sm">
                            <p><strong>Nota:</strong> Esta acción borrará o actualizará registros existentes
                                con datos de <code>data/transactions.csv</code> y <code>data/fraud_policies.json</code>.</p>
                        </div>
                        <button
                            onClick={runSimulation}
                            className="btn-primary py-4 px-8 text-xl mx-auto shadow-xl shadow-bcp-blue/20"
                        >
                            <Play size={24} /> Iniciar Simulación por Lotes
                        </button>
                    </>
                )}

                {status === 'loading' && (
                    <div className="space-y-4">
                        <Loader2 size={48} className="animate-spin text-bcp-blue mx-auto" />
                        <p className="text-lg font-medium text-gray-700">{message}</p>
                    </div>
                )}

                {status === 'success' && (
                    <div className="space-y-6">
                        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                            <CheckCircle2 size={32} />
                        </div>
                        <div className="space-y-2">
                            <p className="text-2xl font-bold text-gray-900">¡Lote Procesado!</p>
                            <p className="text-gray-500">{message}</p>
                        </div>
                        <button onClick={() => window.location.href = '/'} className="btn-secondary mx-auto">
                            Ir al Dashboard para ver resultados
                        </button>
                    </div>
                )}

                {status === 'error' && (
                    <div className="space-y-6">
                        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
                            <AlertCircle size={32} />
                        </div>
                        <div className="space-y-2">
                            <p className="text-2xl font-bold text-gray-900">Falla en la simulación</p>
                            <p className="text-red-500">{message}</p>
                        </div>
                        <button onClick={() => setStatus('idle')} className="btn-secondary mx-auto">
                            Reintentar
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Simulator;
