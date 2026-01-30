import os
import concurrent.futures
from typing import Annotated, List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field
from aws_rag_service import rag_service
from web_search_service import web_search_service

# --- State Definition ---

class AgentState(TypedDict):
    transaction: Dict[str, Any]
    customer: Dict[str, Any]
    transaction_id: str
    signals: List[str]
    internal_evidence: List[Dict[str, Any]]
    external_evidence: List[Dict[str, Any]]
    aggregation: str
    debate: Dict[str, str]
    decision: str
    confidence: float
    explanation_customer: str
    explanation_audit: str

# --- LLM Setup ----
llm = ChatBedrock(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_kwargs={"temperature": 0}
)

# --- Agent Nodes ---

def transaction_context_agent(state: AgentState):
    """Analiza señales internas básicas (monto, hora, país, dispositivo)."""
    tx = state["transaction"]
    cust = state["customer"]
    signals = []
    
    print(f"\n[Agent] Transaction Context: Analyzing TX {tx.get('id')}...")
    
    # Simple logic
    if float(tx.get("amount", 0)) > float(cust.get("usual_amount_avg", 0)) * 3:
        signals.append("Monto muy superior al promedio")
    
    # Hour analysis
    usual_hours = cust.get("usual_hours", "")
    if usual_hours:
        try:
            start_h, end_h = map(int, usual_hours.split('-'))
            from datetime import datetime
            ts = tx.get("timestamp")
            dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            if not (start_h <= dt.hour <= end_h):
                signals.append("Horario no habitual")
        except:
            pass
            
    # Country analysis
    usual_countries = [c.strip() for c in cust.get("usual_countries", "").split(',')] if cust.get("usual_countries") else []
    if tx.get("country") and usual_countries and tx.get("country") not in usual_countries:
        signals.append("País inusual")
    
    print(f" -> Detected signals: {signals}")
    return {"signals": signals}

def behavioral_pattern_agent(state: AgentState):
    """Compara con el historial del cliente para detectar anomalías de comportamiento."""
    tx = state["transaction"]
    cust = state["customer"]
    current_signals = state.get("signals", [])
    
    print("[Agent] Behavioral Pattern: Checking history...")
    
    usual_devices = [d.strip() for d in cust.get("usual_devices", "").split(',')] if cust.get("usual_devices") else []
    if tx.get("device_id") and usual_devices and tx.get("device_id") not in usual_devices:
        current_signals.append("Dispositivo desconocido")
        
    print(f" -> Updated signals: {current_signals}")
    return {"signals": current_signals}

def internal_policy_rag_agent(state: AgentState):
    """Consulta políticas internas vía RAG utilizando AWS Bedrock."""
    signals = ", ".join(state.get("signals", []))
    print(f"[Agent] Internal Policy RAG: Retrieving policies for signals: {signals}...")
    
    # Query the RAG service
    query = f"Políticas de fraude para las siguientes señales: {signals}"
    evidence = rag_service.query_policies(query)
    
    if not evidence:
        print(" -> No relevant policies found.")
        # Return a default or empty evidence if nothing found
        return {"internal_evidence": []}
        
    print(f" -> Found {len(evidence)} relevant policies.")
    return {"internal_evidence": evidence}

def external_threat_intel_agent(state: AgentState):
    """Busca amenazas recientes en la web gobernada usando Tavily."""
    tx = state["transaction"]
    merchant_id = tx.get("merchant_id", "Unknown")
    country = tx.get("country", "Unknown")
    
    print(f"[Agent] External Threat Intel: Searching web for Merchant {merchant_id} in {country}...")
    
    query = f"fraud alert merchant {merchant_id} {country} crypto scam"
    evidence = web_search_service.search(query)
    
    if not evidence:
        print(" -> No external threats found.")
        return {"external_evidence": []}
        
    print(f" -> Found {len(evidence)} external evidence items.")
    return {"external_evidence": evidence}

def evidence_aggregation_agent(state: AgentState):
    """Reúne todas las evidencias y genera un resumen consolidado."""
    tx = state["transaction"]
    signals = ", ".join(state["signals"]) if state["signals"] else "Ninguna señal detectada"
    print(f"[Agent] Evidence Aggregation: Consolidating {len(state['signals'])} signals and evidence...")
    
    # Format internal evidence (RAG)
    internal_docs = []
    for doc in state.get("internal_evidence", []):
        internal_docs.append(f"- [Policy {doc.get('policy_id')}] (v{doc.get('version')}): {doc.get('rule')}")
    internal_str = "\n".join(internal_docs) if internal_docs else "No se encontraron políticas internas aplicables."
    
    # Format external evidence (Web Search)
    external_docs = []
    for doc in state.get("external_evidence", []):
        external_docs.append(f"- [Source: {doc.get('source')}] URL: {doc.get('url')} - Summary: {doc.get('summary')}")
    external_str = "\n".join(external_docs) if external_docs else "No se encontraron alertas externas relevantes."
    
    prompt = f"""
    Eres el Agente de Agregación de Evidencias. Tienes la tarea de consolidar toda la información para el comité de decisión.
    
    SEÑALES DETECTADAS:
    {signals}
    
    POLÍTICAS INTERNAS (RAG):
    {internal_str}
    
    CONTEXTO DE TRANSACCIÓN:
    {state['transaction']}
    
    PERFIL HABITUAL DEL CLIENTE:
    {state['customer']}
    
    Resume los hallazgos clave de manera objetiva, resaltando conflictos entre la conducta del cliente y las políticas o alertas externas. Usa las políticas para brindar resultados comparando el contexto de la transacción con las transacciones habituales del usuario.
    TEN EN CUENTA LA MONEDA: Asegúrate de mencionar la moneda correcta ({tx.get('currency', 'PEN')}) al referirte a montos. NO asumas que es USD si la transacción indica otra moneda.
    IMPORTANTE: Usa Markdown estándar para el formato (**negrita**, # encabezados). NO uses etiquetas HTML.
    """
    
    response = llm.invoke(prompt)
    print(f" -> Summary generated ({len(response.content)} chars)")
    return {"aggregation": response.content}

def debate_agents(state: AgentState):
    """Genera argumentos Pro-Fraud vs Pro-Customer en paralelo."""
    agg = state["aggregation"]
    print("[Agent] Debate: Generating arguments in parallel...")
    
    pro_fraud_prompt = f"""
    Actúa como un Investigador Forense de Fraude.
    Basado en esta evidencia consolidada: {agg}
    Argumenta de forma agresiva por qué esta transacción DEBERÍA ser bloqueada o considerada fraude. 
    Encuentra patrones de riesgo y vulnerabilidades.
    """
    
    pro_customer_prompt = f"""
    Actúa como un Defensor de la Experiencia del Cliente (Customer Success).
    Basado en esta evidencia consolidada: {agg}
    Argumenta por qué esta transacción podría ser LEGÍTIMA.
    Considera falsos positivos, comportamiento atípico pero posible, y el impacto en la lealtad del cliente.
    """
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use Sonnet for critical thinking
        future_fraud = executor.submit(llm.invoke, pro_fraud_prompt)
        future_customer = executor.submit(llm.invoke, pro_customer_prompt)
        
        pro_fraud = future_fraud.result().content
        pro_customer = future_customer.result().content
        
    print(" -> Pro-Fraud and Pro-Customer arguments ready.")
    
    return {"debate": {"pro_fraud": pro_fraud, "pro_customer": pro_customer}}

class DecisionResponse(BaseModel):
    decision: str = Field(description="APPROVE, CHALLENGE, or BLOCK")
    confidence: float = Field(description="Confidence level between 0 and 1")
    reasoning: str = Field(description="Internal technical reasoning for the decision")

def decision_arbiter_agent(state: AgentState):
    """Toma la decisión final basada en el debate y la evidencia."""
    agg = state["aggregation"]
    debate = state["debate"]
    signals = state["signals"]
    
    print("[Agent] Decision Arbiter: Making final call...")
    
    prompt = f"""
    Eres el Árbitro Final de Decisiones de Fraude en el BCP.
    Tu misión es balancear el riesgo de pérdida financiera con la experiencia del cliente.
    
    Señales detectadas: {signals}
    Evidencia Consolidada: {agg}
    Argumentos Pro-Fraude: {debate['pro_fraud']}
    Argumentos Pro-Cliente: {debate['pro_customer']}
    
    Determina la acción más apropiada: 
    - APPROVE: Si el riesgo es bajo o hay justificación clara.
    - CHALLENGE: Si hay sospechas pero no son concluyentes (requiere 2FA o validación).
    - BLOCK: Si la evidencia de fraude es abrumadora.
    
    REGLA HITL: Si después de analizar, tu confianza es menor a 0.6 o los argumentos son extremadamente contradictorios, la decisión real será ESCALATE_TO_HUMAN, pero primero indica qué inclinarías hacer.
    """
    
    # Use Sonnet for the final decision
    structured_llm = llm.with_structured_output(DecisionResponse)
    result = structured_llm.invoke(prompt)
    
    final_decision = result.decision
    confidence = result.confidence
    
    # HITL Logic: Scalate if confidence is low
    if confidence < 0.6:
        print(f" -> Confidence too low ({confidence}). Escalating to human.")
        final_decision = "ESCALATE_TO_HUMAN"
    
    print(f" -> Result: {final_decision} (Initial suggestion: {result.decision}, Confidence: {result.confidence})")
    
    return {
        "decision": final_decision, 
        "confidence": confidence, 
        "explanation_audit": result.reasoning
    }

def explainability_agent(state: AgentState):
    """Genera explicaciones para cliente y auditoría en paralelo."""
    decision = state["decision"]
    signals = state["signals"]
    reasoning = state["explanation_audit"]
    
    print("[Agent] Explainability: Generating natural language reports in parallel...")
    
    customer_prompt = f"""
    Actúa como un asistente de servicio al cliente del BCP.
    Explica de forma clara y amable por qué su transacción (Estado: {decision}) fue procesada de esta manera.
    Usa un lenguaje no técnico. 
    Evita dar detalles técnicos de seguridad que puedan ayudar a un defraudador.
    
    TEN EN CUENTA LA MONEDA: Si el cliente pagó en {state['transaction'].get('currency', 'PEN')}, asegúrate de que la explicación no lo confunda con otra moneda.

    REGLA DE FORMATO:
    - Usa Markdown estándar: **negrita** para resaltar y saltos de línea normales.
    - NO uses etiquetas HTML como <b> o <br/>.
    """
    
    # Reconstructing the agent path for audit
    agent_path = "Context -> Behavior -> (RAG || Web) -> Aggregation -> (Pro-Fraud || Pro-Customer) -> Arbiter -> (Cust-Exp || Audit-Exp)"
    
    audit_prompt = f"""
    Actúa como un Auditor de Seguridad de IA.
    Genera un reporte técnico detallado para ser incluido en un PDF de auditoría.
    
    Decisión Final: {decision}
    Ruta de Agentes: {agent_path}
    Evidencia Consolidada: {state['aggregation']}
    Razonamiento del Árbitro: {reasoning}
    Señales: {signals}
    
    TEN EN CUENTA LA MONEDA: Asegúrate de usar la moneda correcta ({state['transaction'].get('currency', 'PEN')}) al referirte a montos en el reporte.
    
    REGLA DE FORMATO:
    - Usa Markdown estándar (**negrita**, # encabezados) para estructurar el reporte.
    - NO uses etiquetas HTML como <b> o <br/>.
    - NO generes tablas en texto, describe los datos en formato de lista o párrafo.
    """
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use Haiku for faster reports
        future_cust = executor.submit(llm.invoke, customer_prompt)
        future_audit = executor.submit(llm.invoke, audit_prompt)
        
        exp_cust = future_cust.result().content
        exp_audit = future_audit.result().content
        
    print(" -> Explanations generated.")
    
    return {"explanation_customer": exp_cust, "explanation_audit": exp_audit}

# --- Graph Construction ---

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("context", transaction_context_agent)
    workflow.add_node("behavior", behavioral_pattern_agent)
    workflow.add_node("rag", internal_policy_rag_agent)
    workflow.add_node("web", external_threat_intel_agent)
    workflow.add_node("aggregation", evidence_aggregation_agent)
    workflow.add_node("debate", debate_agents)
    workflow.add_node("arbiter", decision_arbiter_agent)
    workflow.add_node("explain", explainability_agent)
    
    # Define edges with Parallel Execution:
    # workflow.set_entry_point("context")
    # context -> behavior -> [rag, web] -> aggregation -> debate -> arbiter -> explain -> END
    
    workflow.set_entry_point("context")
    workflow.add_edge("context", "behavior")
    
    # Parallelize RAG and Web Search
    workflow.add_edge("behavior", "rag")
    workflow.add_edge("behavior", "web")
    
    # Both must finish before aggregation
    workflow.add_edge("rag", "aggregation")
    workflow.add_edge("web", "aggregation")
    
    workflow.add_edge("aggregation", "debate")
    workflow.add_edge("debate", "arbiter")
    workflow.add_edge("arbiter", "explain")
    workflow.add_edge("explain", END)
    
    return workflow.compile()

graph = create_graph()
