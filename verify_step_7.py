import requests
import json

def test_orchestration():
    url = "http://localhost:5001/orchestrate"
    
    # Test case: High risk (Should probably BLOCK or CHALLENGE)
    payload = {
        "transaction": {
            "id": "T-1002",
            "amount": "9500",
            "currency": "PEN",
            "timestamp": "2026-01-28T23:45:00",
            "merchant_id": "M-002",
            "country": "PE",
            "device_id": "D-02"
        },
        "customer": {
            "id": "C-123",
            "usual_amount_avg": "2000",
            "usual_hours": "08-18",
            "usual_countries": "PE",
            "usual_devices": "D-01"
        }
    }

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("\n--- Orchestration Response ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Basic validation
        required_fields = [
            "decision", "confidence", "signals", 
            "citations_internal", "citations_external", 
            "explanation_customer", "explanation_audit"
        ]
        
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"\n❌ Faltan campos en la respuesta: {missing}")
        else:
            print("\n✅ Todos los campos requeridos están presentes.")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_orchestration()
