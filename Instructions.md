A continuación tienes una **secuencia de procedimientos (en orden)** para construir la **web app (Backend + Frontend)** del sistema **multi-agente de detección de fraude** con **Python**, usando **Django + Flask**, e incluyendo **RAG**, **búsqueda web gobernada**, **HITL**, **audit trail**, **confianza** y **explicaciones**, tal como pide el desafío.  

---

## 1) Definir arquitectura y repositorio (base de trabajo)

**Procedimiento**

1. Crear repo (mono-repo recomendado) con 3 componentes:

   * `backend-django/` (API principal + modelos + auditoría + cola HITL + auth).
   * `agents-flask/` (servicio de orquestación multi-agente y ejecución IA).
   * `frontend/` (UI para monitoreo, detalle por transacción y cola HITL).

**Herramientas**

* Python 3.12+, uv, Docker, GitHub.
* Django + Django REST Framework (API), Flask (microservicio de agentes).
* Testing/lint: pytest, ruff/flake8, black, mypy.
* Observabilidad: OpenTelemetry SDK (para trazas), logging estructurado JSON.

---

## 2) Modelar datos y preparar “ingestión” de archivos sintéticos

**Procedimiento**

1. Definir contratos de entrada: `transactions`, `customer_behavior`, `fraud_policies`. 
2. Implementar **parser/loader** (comando Django `manage.py` o endpoint admin) que:

   * Procese los archivos entregados.
   * Consolide por `transaction_id` + `customer_id`. 
3. Persistir en BD:

   * `Transaction`, `CustomerProfile` (comportamiento), `PolicyDocument` (políticas), `DecisionRecord`, `AuditEvent`, `HumanReviewCase`.

**Herramientas**

* Django ORM + migraciones.
* PostgreSQL (AWS RDS/Aurora) como base transaccional.

---

## 3) Implementar análisis de señales (features) y escenarios de decisión

**Procedimiento**

1. Implementar cálculo de señales clave por transacción:

   * Monto vs promedio habitual, horario vs rango habitual, país, dispositivo, canal, patrón de comportamiento. 
2. Normalizar señales a un esquema común para auditoría:

   * `signals[]` (strings/IDs), `features{...}`, `risk_factors[]`.
3. Definir los **4 escenarios** mínimos:

   * `APPROVE`, `CHALLENGE`, `BLOCK`, `ESCALATE_TO_HUMAN`. 

**Herramientas**

* Librerías Python estándar (datetime, statistics), pydantic para validación.
* Django services layer (o “use cases”) para mantener lógica limpia.

---

## 4) Diseñar el equipo multi-agente y la orquestación (Flask)

**Procedimiento**

1. Definir agentes (interfaces + responsabilidades) exactamente como solicita el reto:

   * Transaction Context Agent, Behavioral Pattern Agent, Internal Policy RAG Agent, External Threat Intel Agent, Evidence Aggregation Agent, Debate Agents (Pro-Fraud vs Pro-Customer), Decision Arbiter Agent, Explainability Agent. 
2. Implementar una **secuencia de ejecución** y “handoffs”:

   * Context → Behavior → RAG → Web → Aggregation → Debate → Arbiter → Explainability (y gate a HITL si aplica). 
3. Devolver resultado con:

   * `decision`, `confidence`, `signals`, `citations_internal`, `citations_external`, `explanation_customer`, `explanation_audit`. 

**Herramientas**

* Flask para exponer `/orchestrate` (interno) y endpoints auxiliares.
* Framework de agentes/orquestación (elige 1): LangChain o Bedrock Agents (si usas Bedrock en AWS). 

---

## 5) Implementar RAG de políticas internas (base vectorial)

**Procedimiento**

1. Ingestar `fraud_policies` como documentos (chunking + metadatos `policy_id`, `version`). 
2. Generar embeddings y almacenar en un **vector store**.
3. En el **Internal Policy RAG Agent**:

   * Consultar por señales detectadas (ej. “monto > 3x y horario fuera de rango”).
   * Retornar citas internas con `policy_id`, `chunk_id`, `version`. 

**Herramientas (AWS)**

* **Amazon Bedrock** (embeddings + LLM) o embeddings OSS (si prefieres) dentro de contenedor.
* Vector DB (solo AWS):

  * **Amazon OpenSearch Serverless (Vector Engine)** o
  * **Amazon Aurora PostgreSQL con pgvector**.

---

## 6) Implementar “External Threat Intel” con búsqueda web gobernada

**Procedimiento**

1. Crear un “Web Search Gateway” (servicio interno) que:

   * Aplique allowlist de dominios/fuentes, rate limiting, logging y caching.
   * Devuelva: `url`, `summary`, `timestamp`, `source`.  
2. En el **External Threat Intel Agent**:

   * Consultar por `merchant_id`, país, patrón, keywords (ej. “fraud alert merchant M-002”).
   * Adjuntar `citations_external[]` al expediente.

**Herramientas (AWS)**

* **API Gateway** + **AWS Lambda** (gateway gobernado).
* **VPC + NAT Gateway** + **AWS Network Firewall** (controles de egreso) para “gobernanza”.
* **DynamoDB** (cache de respuestas) + **CloudWatch Logs** (trazabilidad).

---

## 7) Agregación de evidencias, debate y decisión final (con confianza)

**Procedimiento**

1. Evidence Aggregation Agent:

   * Unificar señales internas + políticas RAG + hallazgos externos. 
2. Debate Agents:

   * Generar argumentos “Pro-Fraud” y “Pro-Customer” (máximo trazable).
3. Decision Arbiter Agent:

   * Asignar `decision` y `confidence` (0–1) y explicar ruta tomada. 
4. Reglas HITL:

   * Si `confidence` baja o señales contradictorias ⇒ `ESCALATE_TO_HUMAN` y crear caso en cola. 

**Herramientas**

* Amazon Bedrock (LLM) para debate/explicaciones, o LLM self-hosted en ECS (si lo prefieres, pero Bedrock simplifica).
* Persistencia de `DecisionRecord` + `AuditEvent` (Django).

---

## 8) Human-in-the-loop: cola, revisión y cierre con audit trail

**Procedimiento**

1. Crear “Case Queue”:

   * Cada decisión `ESCALATE_TO_HUMAN` genera un `HumanReviewCase` con estado `OPEN`. 
2. UI de analistas:

   * Listado de casos, detalle con evidencias y acción (approve/challenge/block).
3. Registrar audit trail:

   * Quién revisó, cuándo, decisión humana, y qué evidencias vio.

**Herramientas (AWS)**

* **Amazon SQS** (cola de casos) + **DynamoDB o RDS** (estado).
* **Amazon Cognito** (login/roles para analistas).
* **CloudWatch** + (opcional) **AWS QLDB** si quieres inmutabilidad fuerte del audit trail.

---

## 9) Backend en Django: APIs y contrato de respuesta

**Procedimiento**

1. Endpoints recomendados:

   * `POST /transactions/analyze` (ingresa transacción, dispara orquestación).
   * `GET /transactions/{id}` (detalle + explicación).
   * `GET /hitl/cases` y `POST /hitl/cases/{id}/resolve`.
2. Respuesta estándar por transacción (exactamente el formato pedido). 

**Herramientas**

* Django REST Framework + OpenAPI/Swagger.
* Validación con pydantic/DRF serializers.

---

## 10) Frontend: consola de monitoreo + detalle + HITL

**Procedimiento**

1. Pantallas mínimas:

   * Dashboard: transacciones recientes con decisión/confianza.
   * Detalle: señales + citas internas/externas + explicación cliente/auditor.
   * Cola HITL: bandeja, detalle, acción y comentario.
2. Integración con auth (Cognito) y APIs Django.

**Herramientas (AWS + stack típico)**

* SPA (React/Vue) o Django templates (si quieres rápido).
* Hosting: **S3 Static Website + CloudFront**.
* WAF opcional: **AWS WAF** frente a CloudFront.

---

## 11) Observabilidad, trazabilidad y evidencia para evaluación

**Procedimiento**

1. Log estructurado por “ruta de agentes” (trace_id por transacción).
2. Persistir:

   * Señales detectadas, evidencias RAG y web, decisiones intermedias y final. 
3. Exportar ejemplos:

   * Generar informe IA para al menos 4 transacciones (una por cada decisión). 

**Herramientas (AWS)**

* CloudWatch Logs + CloudWatch Metrics
* AWS X-Ray (trazas) o OpenTelemetry → CloudWatch

---

## 12) Despliegue en AWS (solo servicios AWS) + DevOps

**Procedimiento**

1. Contenerizar:

   * `backend-django` y `agents-flask` como imágenes Docker.
2. Infraestructura:

   * VPC privada, subnets, SG, ALB.
3. Cómputo:

   * **ECS Fargate** para Django y Flask.
4. Datos:

   * **RDS/Aurora PostgreSQL** (transaccional) + (OpenSearch/Aurora pgvector) para RAG.
5. CI/CD + IaC:

   * Terraform/CloudFormation, GitHub Actions o CodePipeline.
   * Secrets: **AWS Secrets Manager**.
   * Registro imágenes: **ECR**.
6. Publicación frontend:

   * S3 + CloudFront.

**Herramientas (según criterios del reto)**

* IaC, CI/CD, secretos, servicios gestionados. 

---

### Resultado esperado (checklist rápido)

* Web App end-to-end (Backend + Frontend). 
* Multi-agentes orquestados, con RAG y web search gobernada.  
* HITL + cola + audit trail. 
* Respuesta por transacción con `decision/confidence/signals/citations/explanations`. 
