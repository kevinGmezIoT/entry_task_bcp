import requests
import json
import time

# Configuración
DJANGO_URL = "http://localhost:8000"
TRANSACTION_ID = "T-1001"
CUSTOMER_ID = "CU-001"

def test_health():
    print("Checking Django health...")
    try:
        resp = requests.get(f"{DJANGO_URL}/health/")
        print(f"Status: {resp.status_code}, Response: {resp.json()}")
    except Exception as e:
        print(f"FAILED: {e}")

def test_analyze():
    print(f"\nTriggering analysis for transaction {TRANSACTION_ID}...")
    payload = {
        "transaction_id": TRANSACTION_ID,
        "customer_id": CUSTOMER_ID
    }
    
    try:
        start_time = time.time()
        resp = requests.post(
            f"{DJANGO_URL}/transactions/analyze/", 
            json=payload,
            timeout=180 # Los agentes pueden tardar bastante
        )
        duration = time.time() - start_time
        
        print(f"Analysis completed in {duration:.2f}s")
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print("\n--- FINAL DECISION ---")
            print(f"Decision: {result['decision']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Signals: {result['signals']}")
            print("\nExplanation (Auditor):")
            print(result['explanation_audit'])
            
            if result['decision'] == 'ESCALATE_TO_HUMAN':
                print("\n[HITL] Verification: check HumanReviewCase in Django Admin!")
        else:
            print(f"Error: {resp.text}")
            
    except Exception as e:
        print(f"FAILED to call analysis endpoint: {e}")

if __name__ == "__main__":
    print("=== STEP 8 VERIFICATION SCRIPT ===")
    test_health()
    test_analyze()
