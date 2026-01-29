from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import Transaction, CustomerProfile
from core.services import DecisionService
from core.serializers import DecisionRecordSerializer
import logging

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
