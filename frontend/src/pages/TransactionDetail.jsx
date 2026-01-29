import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldCheck, FileText, Globe, MessageSquare, AlertTriangle, Download } from 'lucide-react';
import api from '../services/api';

const DetailCard = ({ title, icon: Icon, children }) => (
    <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center gap-2 font-bold text-gray-900 border-b border-gray-100 pb-3">
            <Icon size={20} className="text-bcp-blue" />
            {title}
        </div>
        <div className="space-y-3">
            {children}
        </div>
    </div>
);

function TransactionDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get(`/transactions/${id}/`).then(res => {
            setData(res.data);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            // Data dummy for preview
            setData({
                transaction_id: id,
                customer_id: 'C-MOCK-101',
                decision: 'BLOCK',
                confidence: 0.94,
                signals: ['Monto elevado', 'Horario inusual', 'Nueva ubicación'],
                citations_internal: [
                    { policy_id: 'POL-001', rule: 'Transacciones > $4000 requieren validación 2FA', version: '1.2' }
                ],
                citations_external: [
                    { source: 'ThreatIntel', summary: 'Usuario reportó robo de credenciales en foro externo.', url: 'http://example.com' }
                ],
                explanation_customer: 'Bloqueamos esta transacción por seguridad debido a un monto inusual.',
                explanation_audit: 'El agente detectó anomalía conductual + coincidencia con política POL-001.'
            });
            setLoading(false);
        });
    }, [id]);

    const handleDownload = () => {
        if (!id) return;
        const url = `${api.defaults.baseURL}/reports/${id}/pdf/`;
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Reporte_Fraude_${id}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const renderFormatted = (text) => {
        if (!text) return null;
        return text.split('\n').map((line, i) => (
            <React.Fragment key={i}>
                {line.startsWith('#') ? (
                    <b className="text-gray-900 mt-2 block uppercase text-xs">{line.replace(/^#+\s*/, '')}</b>
                ) : (
                    line.split('**').map((part, j) => (
                        j % 2 === 1 ? <b key={j} className="text-gray-900">{part}</b> : part
                    ))
                )}
                <br />
            </React.Fragment>
        ));
    };

    if (loading) return <div>Cargando...</div>;

    return (
        <div className="space-y-8">
            <button onClick={() => navigate(-1)} className="btn-secondary">
                <ArrowLeft size={18} />
                Volver
            </button>

            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold">Detalle de Transacción: {id}</h2>
                    <div className="flex gap-4 mt-2">
                        <span className={`px-4 py-1 rounded-full text-sm font-bold ${data.decision === 'APPROVE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            DECISIÓN: {data.decision}
                        </span>
                        <span className="px-4 py-1 rounded-full text-sm font-bold bg-green-100 text-green-700">
                            CONFIANZA: {(data.confidence * 100).toFixed(0)}%
                        </span>
                    </div>
                </div>
                <button
                    onClick={handleDownload}
                    className="btn-primary flex items-center gap-2"
                >
                    <Download size={18} />
                    Descargar Informe PDF
                </button>
            </div>

            {data.transaction?.customer && (
                <DetailCard title="Comparativa de Comportamiento" icon={FileText}>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                                <tr>
                                    <th className="px-4 py-2">Métrica</th>
                                    <th className="px-4 py-2 text-bcp-blue">Transacción Actual</th>
                                    <th className="px-4 py-2 text-gray-500">Perfil Habitual</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                <tr>
                                    <td className="px-4 py-3 font-semibold text-gray-600">Monto</td>
                                    <td className="px-4 py-3 font-bold">{data.transaction.amount} {data.transaction.currency}</td>
                                    <td className="px-4 py-3 text-gray-500">~{data.transaction.customer.usual_amount_avg} PEN (Promedio)</td>
                                </tr>
                                <tr>
                                    <td className="px-4 py-3 font-semibold text-gray-600">Horario</td>
                                    <td className="px-4 py-3 font-bold">{new Date(data.transaction.timestamp).getHours()}:00 hrs</td>
                                    <td className="px-4 py-3 text-gray-500">{data.transaction.customer.usual_hours} hrs</td>
                                </tr>
                                <tr>
                                    <td className="px-4 py-3 font-semibold text-gray-600">País</td>
                                    <td className="px-4 py-3 font-bold">{data.transaction.country}</td>
                                    <td className="px-4 py-3 text-gray-500">{data.transaction.customer.usual_countries}</td>
                                </tr>
                                <tr>
                                    <td className="px-4 py-3 font-semibold text-gray-600">Dispositivo</td>
                                    <td className="px-4 py-3 font-bold truncate max-w-[150px]">{data.transaction.device_id}</td>
                                    <td className="px-4 py-3 text-gray-500">{data.transaction.customer.usual_devices}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </DetailCard>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <DetailCard title="Señales Detectadas" icon={AlertTriangle}>
                    <div className="flex flex-wrap gap-2">
                        {data.signals.map((s, i) => (
                            <span key={i} className="px-3 py-1 bg-gray-100 rounded-lg text-sm">{s}</span>
                        ))}
                    </div>
                </DetailCard>

                <DetailCard title="Políticas RAG (Interno)" icon={ShieldCheck}>
                    {data.citations_internal.map((c, i) => (
                        <div key={i} className="bg-blue-50/50 p-3 rounded-xl border border-blue-100">
                            <p className="text-xs font-bold text-blue-800 uppercase">{c.policy_id} (v{c.version})</p>
                            <p className="text-sm mt-1">{c.rule}</p>
                        </div>
                    ))}
                </DetailCard>

                <DetailCard title="Amenazas Externas (Web)" icon={Globe}>
                    {data.citations_external.map((c, i) => (
                        <div key={i} className="bg-orange-50/50 p-3 rounded-xl border border-orange-100">
                            <p className="text-xs font-bold text-orange-800 uppercase">{c.source}</p>
                            <p className="text-sm mt-1">{c.summary}</p>
                            <a href={c.url} target="_blank" className="text-xs text-blue-600 underline mt-2 inline-block">Ver fuente</a>
                        </div>
                    ))}
                </DetailCard>

                <DetailCard title="Explicaciones IA" icon={MessageSquare}>
                    <div className="space-y-4">
                        <div>
                            <p className="text-xs font-bold uppercase text-gray-400">Para el Cliente:</p>
                            <p className="text-sm italic">"{renderFormatted(data.explanation_customer)}"</p>
                        </div>
                        <div>
                            <p className="text-xs font-bold uppercase text-gray-400">Para Auditoría:</p>
                            <div className="text-sm">{renderFormatted(data.explanation_audit)}</div>
                        </div>
                    </div>
                </DetailCard>
            </div>
        </div>
    );
}

export default TransactionDetail;
