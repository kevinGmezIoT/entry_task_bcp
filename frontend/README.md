# Fraud Guard Frontend (React + Vite)

Este es el frontend del sistema de detección de fraude, desarrollado con React, Vite y TailwindCSS.

## Requisitos Previos

- Node.js (v18+)
- npm o yarn
- Backend de Django corriendo en `localhost:8000`

## Pasos para Probar en Local

1.  **Instalar dependencias**:
    ```bash
    cd frontend
    npm install
    ```

2.  **Configurar el Backend**:
    Asegúrate de haber instalado `django-cors-headers` en tu entorno de Python:
    ```bash
    pip install django-cors-headers
    ```
    *(Ya he configurado `settings.py` para usarlo)*.

3.  **Correr el servidor de desarrollo**:
    ```bash
    npm run dev
    ```
    El frontend estará disponible en `http://localhost:5173`.

4.  **Verificación**:
    - Abre `http://localhost:5173` y verás la **Consola de Monitoreo**.
    - Haz clic en la flecha de una transacción para ver el **Detalle**.
    - Ve a **HITL Queue** en la barra lateral para procesar casos de revisión humana.

---

## Configuración de Hosting en AWS

Para desplegar este frontend de forma profesional en AWS, sigue estos pasos:

### 1. Construir el proyecto
```bash
npm run build
```
Esto generará una carpeta `dist/` con archivos estáticos optimizados.

### 2. AWS S3 (Hosting de Archivos)
- Crea un bucket en S3 (ej. `bc-fraud-frontend-prod`).
- Sube el contenido de `dist/` al bucket.
- Configura el bucket para "Static Website Hosting" o mantenlo privado y úsalo con CloudFront OAI/OAC (Recomendado por seguridad).

### 3. AWS CloudFront (CDN & HTTPS)
- Crea una distribución de CloudFront.
- Configura el **Origin** apuntando al bucket de S3.
- Configura los **Error Responses** para que cualquier error 404 devuelva `index.html` con status 200 (necesario para React Router).
- (Opcional) Agrega un segundo Origin apuntando a tu **ALB/App Runner** del Backend para servir las APIs bajo el mismo dominio (ej. `/api/*`).

### 4. AWS Route 53
- Crea un registro A (Alias) apuntando a la distribución de CloudFront.

---

## Modificaciones Realizadas
- `backend/config/settings.py`: Agregado `corsheaders` y configuración de orígenes permitidos.
- `frontend/`: Creado proyecto completo desde cero con arquitectura modular.