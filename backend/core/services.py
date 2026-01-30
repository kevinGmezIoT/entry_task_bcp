import requests
import logging
from datetime import datetime
from django.conf import settings
from core.models import CustomerProfile, Transaction, DecisionRecord, AuditEvent, HumanReviewCase

logger = logging.getLogger(__name__)

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
    @classmethod
    def apply_decision(cls, transaction: Transaction):
        # 1. Prepare data for the multi-agent orchestrator
        customer = transaction.customer
        payload = {
            "transaction": {
                "id": transaction.transaction_id,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "country": transaction.country,
                "device_id": transaction.device_id,
                "timestamp": transaction.timestamp.isoformat(),
                "merchant_id": transaction.merchant_id
            },
            "customer": {
                "id": customer.customer_id,
                "usual_amount_avg": str(customer.usual_amount_avg),
                "usual_hours": customer.usual_hours,
                "usual_countries": customer.usual_countries,
                "usual_devices": customer.usual_devices
            }
        }

        # 2. Call the Flask Orchestrator
        # Use the orchestrator URL from settings (which defaults to agents.local in production)
        orchestrator_url = settings.ORCHESTRATOR_URL
        
        try:
            logger.info(f"Calling orchestrator for transaction {transaction.transaction_id}")
            response = requests.post(orchestrator_url, json=payload, timeout=300)
            response.raise_for_status()
            agent_result = response.json()
            # Log the received JSON result from agents-flask
            logger.info(f"Received result from orchestrator for TX {transaction.transaction_id}:\n{json.dumps(agent_result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            logger.exception(f"Error calling multi-agent orchestrator: {str(e)}")
            # Fallback to local deterministic logic if agents-flask is down
            return cls._apply_fallback_decision(transaction)

        # 3. Parse Agent Results
        decision = agent_result.get("decision", "ESCALATE_TO_HUMAN")
        confidence = agent_result.get("confidence", 0.0)
        signals = agent_result.get("signals", [])
        citations_internal = agent_result.get("citations_internal", [])
        citations_external = agent_result.get("citations_external", [])
        exp_customer = agent_result.get("explanation_customer", "Revisando transacción...")
        exp_audit = agent_result.get("explanation_audit", "Esperando respuesta de agentes.")

        # 4. Create DecisionRecord
        record, _ = DecisionRecord.objects.update_or_create(
            transaction=transaction,
            defaults={
                'decision': decision,
                'confidence': confidence,
                'signals': signals,
                'citations_internal': citations_internal,
                'citations_external': citations_external,
                'explanation_customer': exp_customer,
                'explanation_audit': exp_audit
            }
        )
        
        # 5. Create Audit Event
        AuditEvent.objects.create(
            transaction=transaction,
            event_type="MULTI_AGENT_DECISION",
            description=f"Multi-agent decision: {decision} with confidence {confidence}",
            metadata={
                "trace_id": agent_result.get("trace_id"),
                "signals": signals,
                "agent_path": "Context -> Behavior -> RAG -> Web -> Aggregation -> Debate -> Arbiter -> Explainability"
            }
        )
        
        # 6. Create HITL case if escalated
        if decision == "ESCALATE_TO_HUMAN":
            HumanReviewCase.objects.get_or_create(
                transaction=transaction,
                defaults={'status': 'OPEN'}
            )
            
        return record

    @classmethod
    def _apply_fallback_decision(cls, transaction: Transaction):
        """Fallback logic if the multi-agent system is unavailable."""
        from core.services import SignalAnalysisService
        signals = SignalAnalysisService.analyze_transaction(transaction)
        
        # Basic heuristic
        if len(signals) >= 3:
            decision, confidence = "BLOCK", 0.8
        elif len(signals) >= 1:
            decision, confidence = "CHALLENGE", 0.6
        else:
            decision, confidence = "APPROVE", 0.9

        record, _ = DecisionRecord.objects.update_or_create(
            transaction=transaction,
            defaults={
                'decision': decision,
                'confidence': confidence,
                'signals': signals,
                'explanation_customer': "Su transacción está siendo procesada.",
                'explanation_audit': f"Fallback decision due to orchestrator timeout. Signals: {signals}"
            }
        )
        return record
