from io import BytesIO
import abc
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import re
from xml.sax.saxutils import escape
from core.models import DecisionRecord

class BaseReportService(abc.ABC):
    @abc.abstractmethod
    def generate(self, decision_record: DecisionRecord) -> BytesIO:
        pass

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Escapes XML and converts basic markdown to ReportLab tags."""
        if not text:
            return ""
        
        # 1. Escape all XML specials first
        text = escape(text)
        
        # 2. Convert bold: **text** -> <b>text</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # 3. Convert headers: # text -> <b>text</b>
        text = re.sub(r'^#+\s*(.*)$', r'<b>\1</b>', text, flags=re.MULTILINE)
        
        # 4. New lines to br
        text = text.replace("\n", "<br/>")
        
        return text

class PDFReportService(BaseReportService):
    def generate(self, decision_record: DecisionRecord) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        content = []
        content.append(Paragraph(f"Informe de Auditoría de Fraude - BCP", title_style))
        content.append(Spacer(1, 12))
        
        # Transaction Summary
        tx = decision_record.transaction
        content.append(Paragraph("Resumen de la Transacción", heading_style))
        tx_data = [
            ["ID Transacción:", tx.transaction_id],
            ["ID Cliente:", tx.customer.customer_id],
            ["Monto:", f"{tx.amount} {tx.currency}"],
            ["País:", tx.country],
            ["Dispositivo:", tx.device_id],
            ["Fecha/Hora:", tx.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        ]
        t1 = Table(tx_data, colWidths=[150, 300])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(t1)
        content.append(Spacer(1, 12))
        
        # Decision Info
        content.append(Paragraph("Evaluación del Sistema Multi-Agente", heading_style))
        decision_color = colors.green if decision_record.decision == 'APPROVE' else colors.red if decision_record.decision == 'BLOCK' else colors.orange
        
        decision_label = escape(decision_record.decision)
        decision_data = [
            ["Decisión:", Paragraph(f"<b>{decision_label}</b>", ParagraphStyle('res', textColor=decision_color))],
            ["Confianza:", f"{decision_record.confidence * 100:.2f}%"],
        ]
        t2 = Table(decision_data, colWidths=[150, 300])
        t2.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(t2)
        content.append(Spacer(1, 12))
        
        # Signals
        content.append(Paragraph("Señales Detectadas", heading_style))
        signals_list = [self._clean_markdown(s) for s in decision_record.signals] if decision_record.signals else []
        signals_text = ", ".join(signals_list) if signals_list else "Ninguna señal de riesgo detectada."
        content.append(Paragraph(signals_text, normal_style))
        content.append(Spacer(1, 12))
        
        # Evidence sections (RAG & Web)
        for title, citations in [("Evidencia Interna (RAG)", decision_record.citations_internal), 
                                 ("Inteligencia Externa", decision_record.citations_external)]:
            content.append(Paragraph(title, heading_style))
            if citations:
                for cit in citations:
                    cit_title = self._clean_markdown(cit.get('policy_id') or cit.get('source') or "Evidencia")
                    # Support both 'rule' (RAG) and 'text' (legacy/other)
                    cit_body = self._clean_markdown(cit.get('rule') or cit.get('text') or cit.get('summary') or "")
                    text = f"<b>{cit_title}</b>: {cit_body}"
                    content.append(Paragraph(text, normal_style))
            else:
                content.append(Paragraph("No se encontró evidencia relevante.", normal_style))
            content.append(Spacer(1, 12))
        
        # Explanations
        content.append(Paragraph("Explicación para Auditoría", heading_style))
        content.append(Paragraph(self._clean_markdown(decision_record.explanation_audit), normal_style))
        content.append(Spacer(1, 12))
        
        content.append(Paragraph("Comunicación al Cliente", heading_style))
        content.append(Paragraph(self._clean_markdown(decision_record.explanation_customer), normal_style))
        
        content.append(Spacer(1, 24))
        content.append(Paragraph(f"Documento generado automáticamente por el Sistema de Detección de Fraude BCP.", styles['Italic']))
        
        doc.build(content)
        buffer.seek(0)
        return buffer

class ExcelReportService(BaseReportService):
    def generate(self, decision_record: DecisionRecord) -> BytesIO:
        # Placeholder para futura implementación con pandas/openpyxl
        raise NotImplementedError("Exportación a Excel no implementada aún.")

class WordReportService(BaseReportService):
    def generate(self, decision_record: DecisionRecord) -> BytesIO:
        # Placeholder para futura implementación con python-docx
        raise NotImplementedError("Exportación a Word no implementada aún.")

class ReportFactory:
    @staticmethod
    def get_service(format: str) -> BaseReportService:
        services = {
            'pdf': PDFReportService(),
            'excel': ExcelReportService(),
            'word': WordReportService()
        }
        return services.get(format.lower(), PDFReportService())
