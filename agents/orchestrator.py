import os
from typing import Annotated, List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field
from aws_rag_service import rag_service

# --- State Definition ---

class AgentState(TypedDict):
    transaction: Dict[str, Any]
    customer: Dict[str, Any]
    signals: List[str]
    internal_evidence: List[Dict[str, Any]]
    external_evidence: List[Dict[str, Any]]
    aggregation: str
    debate: Dict[str, str]
    decision: str
    confidence: float
    explanation_customer: str
    explanation_audit: str

# --- LLM Setup ---
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
            
    if tx.get("country") != cust.get("usual_countries"):
        signals.append("País inusual")
    
    print(f" -> Detected signals: {signals}")
    return {"signals": signals}

def behavioral_pattern_agent(state: AgentState):
    """Compara con el historial del cliente para detectar anomalías de comportamiento."""
    tx = state["transaction"]
    cust = state["customer"]
    current_signals = state.get("signals", [])
    
    print("[Agent] Behavioral Pattern: Checking history...")
    
    if tx.get("device_id") != cust.get("usual_devices"):
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
    """Busca amenazas recientes en la web gobernada. (Mock para Paso 6)"""
    print("[Agent] External Threat Intel: Searching web...")
    return {"external_evidence": [{"url": "https://threat-intel.bcp.com.pe/alerts/M-002", "summary": "Alerta de fraude reciente en el merchant detectada en redes externas."}]}

def evidence_aggregation_agent(state: AgentState):
    """Reúne todas las evidencias y genera un resumen consolidado."""
    signals = ", ".join(state["signals"])
    print(f"[Agent] Evidence Aggregation: Consolidating {len(state['signals'])} signals and evidence...")
    internal = str(state["internal_evidence"])
    external = str(state["external_evidence"])
    
    prompt = f"Consolida la siguiente evidencia de fraude:\nSeñales: {signals}\nInterna: {internal}\nExterna: {external}\nGenera un resumen técnico para los agentes de debate."
    response = llm.invoke(prompt)
    print(f" -> Summary generated ({len(response.content)} chars)")
    return {"aggregation": response.content}

def debate_agents(state: AgentState):
    """Genera argumentos Pro-Fraud vs Pro-Customer."""
    agg = state["aggregation"]
    print("[Agent] Debate: Generating arguments...")
    
    pro_fraud_prompt = f"Actúa como un experto en detección de fraude. Basado en esta evidencia: {agg}, argumenta por qué esta transacción DEBERÍA ser bloqueada o considerada fraude."
    pro_customer_prompt = f"Actúa como un defensor del cliente. Basado en esta evidencia: {agg}, argumenta por qué esta transacción podría ser LEGÍTIMA (falso positivo)."
    
    pro_fraud = llm.invoke(pro_fraud_prompt).content
    pro_customer = llm.invoke(pro_customer_prompt).content
    print(" -> Pro-Fraud and Pro-Customer arguments ready.")
    
    return {"debate": {"pro_fraud": pro_fraud, "pro_customer": pro_customer}}

class DecisionResponse(BaseModel):
    decision: str = Field(description="APPROVE, CHALLENGE, BLOCK, or ESCALATE_TO_HUMAN")
    confidence: float = Field(description="Confidence level between 0 and 1")
    reasoning: str = Field(description="Brief technical reasoning for the decision")

def decision_arbiter_agent(state: AgentState):
    """Toma la decisión final basada en el debate y la evidencia."""
    agg = state["aggregation"]
    debate = state["debate"]
    print("[Agent] Decision Arbiter: Making final call...")
    
    prompt = f"""
    Eres el Árbitro de Decisiones de Fraude. Analiza la evidencia y el debate.
    
    Evidencia Consolidada: {agg}
    Argumentos Pro-Fraude: {debate['pro_fraud']}
    Argumentos Pro-Cliente: {debate['pro_customer']}
    
    Determina la acción más apropiada según las políticas de riesgo.
    """
    
    structured_llm = llm.with_structured_output(DecisionResponse)
    result = structured_llm.invoke(prompt)
    print(f" -> Result: {result.decision} (Confidence: {result.confidence})")
    
    return {
        "decision": result.decision, 
        "confidence": result.confidence, 
        "explanation_audit": result.reasoning
    }

def explainability_agent(state: AgentState):
    """Genera explicaciones para cliente y auditoría."""
    decision = state["decision"]
    signals = state["signals"]
    reasoning = state["explanation_audit"]
    print("[Agent] Explainability: Generating natural language reports...")
    
    customer_prompt = f"Genera una explicación amigable para el cliente de por qué su transacción resultó en: {decision}. Señales detectadas: {signals}."
    audit_prompt = f"Genera un reporte técnico de auditoría detallando la ruta de agentes y las evidencias clave para la decisión {decision}. Evidencia: {state['aggregation']}. Razonamiento: {reasoning}"
    
    exp_cust = llm.invoke(customer_prompt).content
    exp_audit = llm.invoke(audit_prompt).content
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
    
    # Define edges (Sequential as requested)
    workflow.set_entry_point("context")
    workflow.add_edge("context", "behavior")
    workflow.add_edge("behavior", "rag")
    workflow.add_edge("rag", "web")
    workflow.add_edge("web", "aggregation")
    workflow.add_edge("aggregation", "debate")
    workflow.add_edge("debate", "arbiter")
    workflow.add_edge("arbiter", "explain")
    workflow.add_edge("explain", END)
    
    return workflow.compile()

graph = create_graph()
