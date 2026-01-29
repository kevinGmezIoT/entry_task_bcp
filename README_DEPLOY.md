# Guía de Despliegue en AWS - Entry Task BCP

Este proyecto utiliza **AWS CDK** para la Infraestructura como Código (IaC) y **AWS CodePipeline** para CI/CD.

## Arquitectura de Despliegue

- **Frontend**: React (Vite) alojado en **S3** y distribuido mediante **CloudFront**.
- **Backend (Django)**: Escala en **ECS Fargate** con un **Application Load Balancer**.
- **Agentes (Flask)**: Escala en **ECS Fargate** (microservicio separado).
- **Secretos**: Integración con **AWS Secrets Manager** y **AWS Systems Manager Parameter Store**.
- **CI/CD**: Tubería automatizada que construye imágenes Docker y despliega todo al realizar push a `master`.

---

## 1. Requisitos Previos

1.  **AWS CLI** configurado con credenciales.
2.  **Node.js** y **Python 3.12** instalados.
3.  **GitHub Token**: Crear un Personal Access Token con permisos `repo` y `admin:repo_hook`. guardarlo en **AWS Secrets Manager** con el nombre `GITHUB-TOKEN` (formato texto plano).

---

## 2. Configuración de Secretos y Parámetros

Antes del primer despliegue, debes configurar los siguientes valores en AWS:

### Secrets Manager (Nombre del secreto exacto)
- `GITHUB-TOKEN`: Tu token de GitHub.
- `TAVILY_API_KEY`: API Key para búsqueda web.
- `LANGCHAIN_API_KEY`: API Key para LangSmith/LangChain.
- `DJANGO_SECRET_KEY`: La clave secreta de tu aplicación Django.

### Parameter Store (Ejemplo para entorno DEV)
- `/entry-task/DEV/django-debug`: `1` o `0`.
- `/entry-task/DEV/database-url`: URL de conexión a PostgreSQL (ej. `postgresql://user:pass@host:5432/db`).
- `/entry-task/DEV/bedrock-kb-id`: ID de tu Knowledge Base de Bedrock.
- `/entry-task/DEV/bedrock-ds-id`: ID de tu Data Source de Bedrock.



---

## 3. Comandos para Probar Docker Localmente

Para validar los Dockerfiles antes de desplegar:

### Backend
```bash
cd backend
docker build -t bcp-fraud-backend .
# Ejecutar localmente (requiere configurar ENV o archivo .env)
docker run -p 8000:8000 --env-file ../.env bcp-fraud-backend
```

### Agentes
```bash
cd agents
docker build -t bcp-fraud-agents .
# Ejecutar localmente pasando credenciales de AWS
docker run -p 5001:5001 --env-file ../.env -e AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID% -e AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY% -e AWS_SESSION_TOKEN=%AWS_SESSION_TOKEN% bcp-fraud-agents
```

> [!TIP]
> Si estás en Linux/Mac, usa `$AWS_ACCESS_KEY_ID` en lugar de `%AWS_ACCESS_KEY_ID%`.


---

## 5. Despliegue Inicial de la Infraestructura

Ejecuta estos comandos desde la raíz del proyecto para levantar la tubería CI/CD:

```bash
# Instalar dependencias del CDK (si no lo has hecho)
cd cdk
pip install -r requirements.txt
npm install -g aws-cdk

# Desplegar la tubería (Pipeline) usando un perfil específico de AWS
cdk deploy --all -c environment=DEV --profile TU_PERFIL_AWS
```

> [!NOTE]
> Si no especificas `--profile`, CDK usará el perfil `default` configurado en tus credenciales locales. Alternativamente, puedes usar la variable de entorno `export AWS_PROFILE=TU_PERFIL`.


Una vez que el Pipeline esté creado, cualquier push a la rama `master` de tu repositorio disparará automáticamente:
1.  Construcción de imágenes Docker (Backend y Agentes).
2.  Push a **Amazon ECR**.
3.  Build de React Frontend.
4.  Sincronización a **S3**.
5.  Actualización de servicios en **ECS Fargate**.

---

## 6. Verificación y Operaciones Post-Despliegue

Una vez que el Pipeline termine (puedes monitorearlo en la consola de **AWS CodePipeline**), ejecuta estos pasos para validar todo:

### A. Verificar Salud de los Servicios
Obtén las URLs de los outputs de CloudFormation o de la pestaña "Outputs" del stack `App` en CDK.

- **Frontend**: Abre la URL de CloudFront en tu navegador.
- **Backend Health**: `curl https://<TU_URL_ALB>/api/health/`
- **Agents Health**: `curl https://<TU_URL_ALB>:5001/health` (si el puerto está expuesto) o verifica en ECS CloudWatch Logs.

### B. Sincronización Manual de RAG (Políticas)
Si modificas `data/fraud_policies.json` y quieres actualizar el RAG en la nube sin esperar al pipeline (o como primer paso):

```bash
# Entrar al contenedor del Backend en ECS (usando AWS CLI)
# Primero obtén el ID del cluster y la tarea
aws ecs list-tasks --cluster EntryClusterBcp-DEV

# Ejecutar los comandos de Django
aws ecs execute-command --cluster EntryClusterBcp-DEV \
    --task <TASK_ID> \
    --container BackendContainer \
    --interactive \
    --command "python manage.py seed_data"

aws ecs execute-command --cluster EntryClusterBcp-DEV \
    --task <TASK_ID> \
    --container BackendContainer \
    --interactive \
    --command "python manage.py ingest_rag"
```

> [!IMPORTANT]
> Para usar `execute-command`, debes tener instalada la extensión `session-manager-plugin` de AWS CLI en tu máquina local.

### C. Verificar Logs
Si algo falla, la fuente de verdad son los logs:
- **CloudWatch Logs**: Busca los grupos `/aws/ecs/EntryTaskBcp...` para ver la salida de Django y Flask.

### D. Probar Flujo Completo
Usa el script de prueba local ajustando la URL:
```bash
python verify_step_8.py --url https://<TU_URL_ALB>
```
