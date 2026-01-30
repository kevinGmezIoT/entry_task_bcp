# 🚀 Guía de Despliegue y Configuración Local - BCP Fraud Detection

Esta guía proporciona instrucciones detalladas para configurar el entorno de desarrollo local y desplegar la infraestructura en AWS. Está diseñada para que un nuevo desarrollador pueda poner en marcha el proyecto desde cero.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

1.  **Python 3.12+** y [uv](https://docs.astral.sh/uv/) (recomendado para gestión de dependencias).
2.  **Node.js 20+** y `npm`.
3.  **Docker Desktop** (para probar contenedores localmente).
4.  **AWS CLI** configurado con credenciales válidas.
5.  **AWS CDK CLI** (`npm install -g aws-cdk`).

---

## 💻 1. Configuración Local (Paso a Paso)

### A. Clonar y Variables de Entorno
1.  Clona el repositorio.
2.  Crea un archivo `.env` en la raíz del proyecto basado en el siguiente ejemplo:

```env
# Django
DJANGO_SECRET_KEY=tu_clave_secreta
DJANGO_DEBUG=1
DATABASE_URL=sqlite:///db.sqlite3

# AWS (para RAG y Bedrock)
AWS_REGION=us-east-2
BEDROCK_KB_ID=tu_kb_id
BEDROCK_DS_ID=tu_ds_id

# Agentes e Inteligencia Externa
TAVILY_API_KEY=tu_tavily_key
LANGCHAIN_API_KEY=tu_langchain_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=bcp-fraud-detection
```

### B. Backend (Django)
1.  Navega a `backend/`.
2.  Instala dependencias y activa el entorno:
    ```bash
    uv venv
    # En Windows: .venv\Scripts\activate
    uv sync
    ```
3.  Aplica migraciones y carga datos iniciales:
    ```bash
    python manage.py migrate
    python manage.py seed_data
    ```
4.  Inicia el servidor:
    ```bash
    python manage.py runserver
    ```

### C. Sistema de Agentes (Flask)
1.  Navega a `agents/`.
2.  Instala dependencias:
    ```bash
    uv venv
    uv sync
    ```
3.  Inicia el servicio de orquestación:
    ```bash
    python app.py
    ```
    *Nota: Los agentes correrán por defecto en http://localhost:5001.*

### D. Frontend (React + Vite)
1.  Navega a `frontend/`.
2.  Instala dependencias:
    ```bash
    npm install
    ```
3.  Inicia el modo desarrollo:
    ```bash
    npm run dev
    ```

---

## 🐳 2. Pruebas con Docker

Para validar que los servicios están listos para la nube, puedes usar Docker localmente:

```bash
# Backend
cd backend
docker build -t bcp-backend .
docker run -p 8000:8000 --env-file ../.env bcp-backend

# Agentes
cd agents
docker build -t bcp-agents .
docker run -p 5001:5001 --env-file ../.env bcp-agents
```

---

## ☁️ 3. Despliegue en AWS (CDK)

El despliegue está automatizado con AWS CDK y CodePipeline.

### Configuración de Secretos (Obligatorio)
Antes de desplegar, guarda los siguientes secretos en **AWS Secrets Manager** (nombre exacto):
*   `GITHUB-TOKEN`: Token de acceso personal con permisos de repo.
*   `TAVILY_API_KEY`: Tu API Key de Tavily.
*   `LANGCHAIN_API_KEY`: Tu API Key de LangSmith.

### Despliegue del Pipeline
Desde la raíz del proyecto:
```bash
cd cdk
uv venv
uv sync
cdk deploy --all -c environment=DEV
```

Esto creará:
- **S3 + CloudFront**: Para el frontend estático.
- **ECS Fargate**: Para el Backend y los Agentes.
- **Application Load Balancer (ALB)**: Como punto de entrada.
- **CodePipeline**: Para CI/CD automático en cada `push` a `master`.

---

## 🔍 4. Verificación y Troubleshooting

### Health Checks
- **Frontend**: Accede a la URL de CloudFront (disponible en los outputs de CDK).
- **Backend API**: `GET /api/health/`
- **Agents**: `GET /health`

### Tareas Post-Despliegue
Si necesitas sincronizar el Knowledge Base de Bedrock o reinicializar datos en ECS:
```bash
# Ejemplo: Ejecutar seeding en el contenedor de ECS
aws ecs execute-command --cluster EntryClusterBcp-DEV \
    --task <TASK_ID> --container BackendContainer \
    --interactive --command "python manage.py seed_data"
```

### Logs
- **Local**: Revisa la terminal de cada servicio.
- **AWS**: Busca en **CloudWatch Logs** bajo el grupo `/aws/ecs/EntryTaskBcp`.

---

> [!TIP]
> Si encuentras errores de permisos con Bedrock localmente, asegúrate de que tu perfil de AWS tenga la política `AmazonBedrockFullAccess` o similar.
