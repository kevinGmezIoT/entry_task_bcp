from datetime import datetime
from core.models import CustomerProfile, Transaction, DecisionRecord, AuditEvent, HumanReviewCase

class SignalAnalysisService:
    @staticmethod
    def analyze_transaction(transaction: Transaction):
        signals = []
        customer = transaction.customer
        
        # 1. Amount Analysis
        if float(transaction.amount) > float(customer.usual_amount_avg) * 2:
            signals.append("Monto fuera de rango")
            
        # 2. Hours Analysis
        if customer.usual_hours:
            try:
                start_h, end_h = map(int, customer.usual_hours.split('-'))
                tx_hour = transaction.timestamp.hour
                if not (start_h <= tx_hour <= end_h):
                    signals.append("Horario no habitual")
            except ValueError:
                pass
        
        # 3. Country Analysis
        if customer.usual_countries:
            usual_countries = [c.strip() for c in customer.usual_countries.split(',')]
            if transaction.country not in usual_countries:
                signals.append("País inusual")
                
        # 4. Device Analysis
        if customer.usual_devices:
            usual_devices = [d.strip() for d in customer.usual_devices.split(',')]
            if transaction.device_id not in usual_devices:
                signals.append("Dispositivo desconocido")
                
        return signals

class DecisionService:
    @staticmethod
    def get_decision(signals: list, transaction: Transaction):
        # Simplificamos la lógica de decisión para el paso 3
        # En pasos posteriores esto podría involucrar a los agentes
        if not signals:
            return "APPROVE", 0.95
        
        if len(signals) >= 3:
            return "BLOCK", 0.85
        
        if "Monto fuera de rango" in signals and len(signals) >= 2:
            return "ESCALATE_TO_HUMAN", 0.60
            
        if len(signals) > 0:
            return "CHALLENGE", 0.70
            
        return "APPROVE", 0.90

    @classmethod
    def apply_decision(cls, transaction: Transaction):
        signals = SignalAnalysisService.analyze_transaction(transaction)
        decision, confidence = cls.get_decision(signals, transaction)
        
        # Create DecisionRecord
        record, _ = DecisionRecord.objects.update_or_create(
            transaction=transaction,
            defaults={
                'decision': decision,
                'confidence': confidence,
                'signals': signals,
                'explanation_customer': cls._generate_customer_explanation(decision, signals),
                'explanation_audit': cls._generate_audit_explanation(decision, signals)
            }
        )
        
        # Create Audit Event
        AuditEvent.objects.create(
            transaction=transaction,
            event_type="DECISION_MADE",
            description=f"Decision {decision} made with confidence {confidence}",
            metadata={"signals": signals}
        )
        
        # Create HITL case if escalated
        if decision == "ESCALATE_TO_HUMAN":
            HumanReviewCase.objects.get_or_create(
                transaction=transaction,
                defaults={'status': 'OPEN'}
            )
            
        return record

    @staticmethod
    def _generate_customer_explanation(decision, signals):
        if decision == "APPROVE":
            return "Su transacción ha sido aprobada con éxito."
        if decision == "CHALLENGE":
            return "Su transacción requiere una validación adicional por seguridad."
        if decision == "BLOCK":
            return "Por su seguridad, esta transacción ha sido bloqueada preventivamente."
        if decision == "ESCALATE_TO_HUMAN":
            return "Estamos revisando su transacción. Por favor, espere unos momentos."
        return ""

    @staticmethod
    def _generate_audit_explanation(decision, signals):
        if not signals:
            return "No se detectaron señales de riesgo. Comportamiento habitual."
        signals_str = ", ".join(signals)
        return f"Decisión {decision} basada en las señales: {signals_str}."
