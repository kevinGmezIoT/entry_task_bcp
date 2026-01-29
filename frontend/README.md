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
- **Configuración Recomendada**:
  - Mantén activada la opción **"Block all public access"** (Deseado para OAC).
  - No actives "Static Website Hosting" si usas CloudFront con OAC.
- **Subida de Archivos**:
  - Sube el **contenido** de la carpeta `dist/` a la raíz del bucket.
  - Asegúrate de que `index.html` esté en el primer nivel.

#### Opción AWS CLI (Recomendada):
```bash
aws s3 sync dist/ s3://tu-nombre-de-bucket --delete
```

### 3. AWS CloudFront (CDN & HTTPS)
Este es el método más seguro para servir la aplicación manteniendo el bucket privado.

1.  **Crear Origen (Origin)**:
    - **Origin domain**: Selecciona tu bucket (ej. `nombre.s3.us-east-2.amazonaws.com`).
    - **Origin access**: Selecciona **"Origin access control settings (recommended)"**.
    - Crea un nuevo OAC (mantén los valores por defecto).

2.  **Configuración General**:
    - **Default root object**: Escribe `index.html`. (Sin esto, verás un error XML al entrar a la raíz).

3.  **Permisos en S3 (Bucket Policy)**:
    - Tras crear la distribución, CloudFront te mostrará un mensaje para actualizar la política del bucket.
    - Copia la política y pégala en **S3 -> Permissions -> Bucket Policy**. Debe verse así:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipalReadOnly",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::TU-BUCKET-NOMBRE/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::TU-ID-CUENTA:distribution/TU-ID-DISTRIBUCION"
                }
            }
        }
    ]
}
```

4.  **Manejo de Rutas (Error Pages)**:
    - Ve a la pestaña **Error pages** -> **Create custom error response**.
    - Error code: `404: Not Found`.
    - Response page path: `/index.html`.
    - HTTP Response code: `200: OK`.
    - *(Esto permite que React Router maneje las rutas al recargar la página)*.

### 4. AWS Route 53
- Crea un registro A (Alias) apuntando a la distribución de CloudFront.

---

## Modificaciones Realizadas
- `backend/config/settings.py`: Agregado `corsheaders` y configuración de orígenes permitidos.
- `frontend/`: Creado proyecto completo desde cero con arquitectura modular.