import React, { useState, useEffect } from 'react';
import { FileText, Download, ShieldCheck, ExternalLink, Calendar } from 'lucide-react';
import api from '../services/api';

function Reports() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/reports/').then(res => {
            setReports(res.data);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            // Dummy data for demo if no reports yet
            setReports([
                { id: 1, transaction_id: 'T-001', customer_id: 'C-MOCK-1', decision: 'APPROVE', confidence: 0.98, explanation_audit: 'Análisis completo sin riesgos detectados.', created_at: '2026-01-29' },
                { id: 2, transaction_id: 'T-002', customer_id: 'C-MOCK-2', decision: 'BLOCK', confidence: 0.94, explanation_audit: 'Detección de fraude por suplantación de identidad.', created_at: '2026-01-29' }
            ]);
            setLoading(false);
        });
    }, []);

    const handleDownload = (txId) => {
        if (!txId) return;

        // Call the new PDF endpoint
        const url = `${api.defaults.baseURL}/reports/${txId}/pdf/`;

        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Reporte_Fraude_${txId}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const renderFormatted = (text) => {
        if (!text) return null;
        return text.split('\n').map((line, i) => (
            <React.Fragment key={i}>
                {line.split('**').map((part, j) => (
                    j % 2 === 1 ? <b key={j} className="text-gray-900">{part}</b> : part
                ))}
                <br />
            </React.Fragment>
        ));
    };

    if (loading) return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold text-gray-900">Informes de Auditoría (Step 11)</h2>
                <p className="text-gray-500">Evidencias consolidadas y explicaciones generadas por la IA para fines de reporte.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3].map((_, index) => (
                    <div key={index} className="glass-card animate-pulse rounded-2xl p-6 flex flex-col justify-between h-full">
                        <div className="space-y-4">
                            <div className="flex justify-between items-start">
                                <div className="p-3 bg-gray-100 rounded-xl w-10 h-10"></div>
                                <div className="h-6 bg-gray-100 rounded-full w-20"></div>
                            </div>
                            <div className="space-y-2">
                                <div className="h-5 bg-gray-100 rounded w-3/4"></div>
                                <div className="h-4 bg-gray-100 rounded w-1/2"></div>
                                <div className="h-3 bg-gray-100 rounded w-1/3"></div>
                            </div>
                            <div className="space-y-2">
                                <div className="h-4 bg-gray-100 rounded"></div>
                                <div className="h-4 bg-gray-100 rounded w-5/6"></div>
                                <div className="h-4 bg-gray-100 rounded w-4/6"></div>
                            </div>
                        </div>
                        <div className="pt-6 mt-6 border-t border-gray-100 flex justify-between items-center text-sm">
                            <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                            <div className="flex gap-3">
                                <div className="w-6 h-6 bg-gray-100 rounded-full"></div>
                                <div className="w-16 h-6 bg-gray-100 rounded-full"></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold text-gray-900">Informes de Auditoría (Step 11)</h2>
                <p className="text-gray-500">Evidencias consolidadas y explicaciones generadas por la IA para fines de reporte.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {reports.map((report) => (
                    <div key={report.id} className="glass-card hover:ring-2 hover:ring-bcp-blue/20 transition-all rounded-2xl p-6 flex flex-col justify-between h-full">
                        <div className="space-y-4">
                            <div className="flex justify-between items-start">
                                <div className="p-3 bg-blue-50 text-bcp-blue rounded-xl">
                                    <FileText size={20} />
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${report.decision === 'APPROVE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                    }`}>
                                    {report.decision}
                                </span>
                            </div>
                            <div>
                                <h4 className="font-bold text-lg">Reporte IA: {report.transaction_id}</h4>
                                <p className="text-sm text-bcp-blue font-medium">Cliente: {report.customer_id}</p>
                                <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                                    <Calendar size={12} /> {new Date(report.created_at).toLocaleDateString()}
                                </p>
                            </div>
                            <div className="text-sm text-gray-600 line-clamp-3 mt-1">
                                {renderFormatted(report.explanation_audit)}
                            </div>
                        </div>

                        <div className="pt-6 mt-6 border-t border-gray-100 flex justify-between items-center text-sm">
                            <span className="font-medium text-gray-900">Confianza: {(report.confidence * 100).toFixed(0)}%</span>
                            <div className="flex gap-3">
                                <button
                                    className="text-gray-400 hover:text-bcp-blue transition-colors"
                                    title="Descargar PDF"
                                    onClick={() => handleDownload(report.transaction_id)}
                                >
                                    <Download size={18} />
                                </button>
                                <a href={`/transaction/${report.transaction_id}`} className="text-bcp-blue font-bold flex items-center gap-1">
                                    Detalles <ExternalLink size={14} />
                                </a>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Reports;
