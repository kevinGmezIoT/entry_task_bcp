from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import Transaction, CustomerProfile
from core.services import DecisionService
from core.serializers import DecisionRecordSerializer, TransactionSerializer
from django.core.management import call_command
import logging
import json

logger = logging.getLogger(__name__)

@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})

@api_view(["POST"])
def analyze_transaction(request):
    """
    Endpoint principal para analizar una transacción.
    Espera un JSON con metadata de la transacción y el cliente.
    """
    data = request.data
    transaction_id = data.get("transaction_id")
    customer_id = data.get("customer_id")
    
    if not transaction_id or not customer_id:
        return Response({"error": "transaction_id and customer_id are required"}, status=400)
    
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        # Asegurarse de que el customer_id coincida
        if transaction.customer.customer_id != customer_id:
             return Response({"error": "Customer ID mismatch"}, status=400)
             
        # Ejecutar el flujo de decisión (llama a los agentes)
        decision_record = DecisionService.apply_decision(transaction)
        
        # Devolver el resultado formateado
        serializer = DecisionRecordSerializer(decision_record)
        return Response(serializer.data)
        
    except Transaction.DoesNotExist:
        return Response({"error": f"Transaction {transaction_id} not found"}, status=404)
    except Exception as e:
        logger.exception("Error during transaction analysis")
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def get_transaction_detail(request, transaction_id):
    """
    Obtener el detalle de una transacción y su decisión.
    """
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        decision = getattr(transaction, 'decision', None)
        
        if not decision:
            return Response({"error": "No decision found for this transaction"}, status=404)
            
        serializer = DecisionRecordSerializer(decision)
        return Response(serializer.data)
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=404)

@api_view(["GET"])
def list_hitl_cases(request):
    """
    Listar casos pendientes de revisión humana.
    """
    from core.models import HumanReviewCase
    from core.serializers import HumanReviewCaseSerializer
    
    cases = HumanReviewCase.objects.filter(status='OPEN')
    serializer = HumanReviewCaseSerializer(cases, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def resolve_hitl_case(request, case_id):
    """
    Resolver un caso de revisión humana.
    """
    from core.models import HumanReviewCase
    from django.utils import timezone
    
    try:
        case = HumanReviewCase.objects.get(id=case_id)
        decision = request.data.get("decision")
        notes = request.data.get("notes", "")
        
        if decision not in ['APPROVE', 'CHALLENGE', 'BLOCK']:
            return Response({"error": "Invalid decision. Must be APPROVE, CHALLENGE, or BLOCK"}, status=400)
            
        case.status = 'RESOLVED'
        case.human_decision = decision
        case.notes = notes
        case.resolved_at = timezone.now()
        case.save()
        
        # Actualizar el registro de decisión original
        decision_record = case.transaction.decision
        decision_record.decision = decision
        decision_record.explanation_audit += f"\n[HITL] Decisión humana: {decision}. Notas: {notes}"
        decision_record.save()
        
        return Response({"status": "case resolved", "decision": decision})
    except HumanReviewCase.DoesNotExist:
        return Response({"error": "Case not found"}, status=404)
@api_view(["POST"])
def seed_batch(request):
    """
    Simular carga masiva de datos (Step 2).
    Llama al comando seed_data.
    """
    try:
        call_command('seed_data')
        return Response({"status": "Batch seeding completed successfully"})
    except Exception as e:
        logger.exception("Error during batch seeding")
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def create_manual_transaction(request):
    """
    Registrar una transacción manual y evaluarla (Step 10).
    """
    data = request.data
    try:
        # 1. Obtener o crear cliente
        customer_id = data.get("customer_id", "MANUAL-CUST")
        customer, _ = CustomerProfile.objects.get_or_create(
            customer_id=customer_id,
            defaults={
                'usual_amount_avg': 1000,
                'usual_hours': '09-18',
                'usual_countries': 'PE',
                'usual_devices': 'iPhone'
            }
        )

        # 2. Crear transacción
        from django.utils import timezone
        import uuid
        
        transaction_id = data.get("transaction_id", f"M-{uuid.uuid4().hex[:8]}")
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            customer=customer,
            amount=data.get("amount", 100.0),
            currency=data.get("currency", "PEN"),
            country=data.get("country", "PE"),
            channel=data.get("channel", "MOBILE"),
            device_id=data.get("device_id", "MANUAL-DEV"),
            timestamp=timezone.now(),
            merchant_id=data.get("merchant_id", "M-001")
        )

        # 3. Analizar inmediatamente
        decision_record = DecisionService.apply_decision(transaction)
        
        serializer = DecisionRecordSerializer(decision_record)
        return Response(serializer.data, status=201)
        
    except Exception as e:
        logger.exception("Error during manual transaction creation")
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def get_audit_reports(request):
    """
    Listar informes de auditoría (Step 11).
    Devuelve los registros de decisión que tienen explicaciones.
    """
    from core.models import DecisionRecord
    from core.serializers import DecisionRecordSerializer
    
    # Podríamos filtrar para mostrar uno de cada tipo como pide el reto
    reports = DecisionRecord.objects.all().order_by('-created_at')[:10]
    serializer = DecisionRecordSerializer(reports, many=True)
    return Response(serializer.data)
