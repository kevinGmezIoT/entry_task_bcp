import requests
import json

def test_step_6():
    url = "http://localhost:5001/orchestrate"
    
    payload = {
        "transaction": {
            "id": "TX-999",
            "amount": "5000.00",
            "timestamp": "2026-01-28T22:00:00",
            "country": "PE",
            "device_id": "DEV-ABC",
            "merchant_id": "M-002",
            "channel": "WEB"
        },
        "customer": {
            "id": "CUST-001",
            "usual_amount_avg": "100.00",
            "usual_hours": "09-18",
            "usual_countries": "PE",
            "usual_devices": "DEV-ABC"
        }
    }
    
    print("Enviando transacción para análisis (Paso 6 - Tavily Search)...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("\n=== Resultado de la Orquestación ===")
            print(f"ID: {result.get('trace_id')}")
            print(f"Decisión: {result.get('decision')}")
            print(f"Confianza: {result.get('confidence')}")
            print(f"Señales: {result.get('signals')}")
            
            print("\n--- Evidencia Externa (Tavily) ---")
            ext = result.get('citations_external', [])
            if ext:
                for i, item in enumerate(ext):
                    print(f"{i+1}. {item.get('url')}")
                    print(f"   Resumen: {item.get('summary')[:100]}...")
            else:
                print("No se encontró evidencia externa (revisa tu API Key de Tavily en .env)")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error de conexión: {e}")
        print("Asegúrate de que el servicio de agentes esté corriendo en el puerto 5001.")

if __name__ == "__main__":
    test_step_6()
