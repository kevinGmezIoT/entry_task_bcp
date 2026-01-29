import logging
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables from .env at the root of the project
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

from orchestrator import graph

app = Flask(__name__)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agents-flask")

@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    trace_id = str(uuid.uuid4())
    data = request.json
    
    if not data:
        logger.warning(f"[{trace_id}] No data provided in request")
        return jsonify({"error": "No data provided"}), 400
    
    transaction = data.get("transaction")
    customer = data.get("customer")
    tx_id = transaction.get("id") if transaction else "N/A"
    
    logger.info(f"[{trace_id}] === START Orchestration for TX: {tx_id} ===")
    
    if not transaction or not customer:
        logger.error(f"[{trace_id}] Missing transaction or customer data")
        return jsonify({"error": "Missing transaction or customer data"}), 400
    
    # Initialize State
    initial_state = {
        "transaction": transaction,
        "customer": customer,
        "transaction_id": tx_id,
        "signals": [],
        "internal_evidence": [],
        "external_evidence": [],
        "aggregation": "",
        "debate": {"pro_fraud": "", "pro_customer": ""},
        "decision": "",
        "confidence": 0.0,
        "explanation_customer": "",
        "explanation_audit": ""
    }
    
    try:
        # Run LangGraph Orchestration
        # Tagging for LangSmith
        config = {
            "configurable": {"thread_id": trace_id},
            "metadata": {
                "transaction_id": tx_id,
                "customer_id": customer.get("id", "N/A")
            },
            "tags": ["fraud-detection-v1", f"tx-{tx_id}"]
        }
        result = graph.invoke(initial_state, config)
        
        logger.info(f"[{trace_id}] === END Orchestration. Decision: {result['decision']} (Conf: {result['confidence']}) ===")
        
        # Prepare response
        response = {
            "trace_id": trace_id,
            "decision": result["decision"],
            "confidence": result["confidence"],
            "signals": result["signals"],
            "citations_internal": result["internal_evidence"],
            "citations_external": result["external_evidence"],
            "explanation_customer": result["explanation_customer"],
            "explanation_audit": result["explanation_audit"]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"[{trace_id}] Error during orchestration: {str(e)}")
        return jsonify({"error": str(e), "trace_id": trace_id}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
