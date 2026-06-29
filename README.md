# Backend API - APIVENEZUELAEARTHQUAKE

Este proyecto ha sido generado con una robusta **Arquitectura Hexagonal (Clean Architecture)** enfocada en la alta escalabilidad, mantenimiento simple y máximo rendimiento, desacoplado de dependencias particulares.

Además, cuenta con un **Modo Desarrollo (Development Mode)** integrado para agilizar el flujo de trabajo de los ingenieros de software de forma local o en entornos compartidos.

---

## 🛠️ Arquitectura de Directorios

El backend se estructura de la siguiente manera bajo el principio de separación de responsabilidades:

```
apivenezuelaearthquake_backend/
├── app.py                      # Punto de arranque de la aplicación usando Uvicorn.
├── Dockerfile                  # Empaquetado Docker optimizado en dos fases (Slim).
├── docker-compose.yml          # Define servicios de API y Redis DB de forma local.
├── requirements.txt            # Dependencias actualizadas del ecosistema Python.
├── .env                        # Configuración del entorno de producción.
├── .env.dev                    # Configuración del entorno de desarrollo estructurado.
├── .env.example                # Plantilla de variables de entorno para producción.
└── src_python/
    ├── domain/                 # Capa de Core Logics y Reglas de Negocio.
    │   ├── models.py           # Estructuras de datos (Modelos de entidad).
    │   ├── repository_ports.py # Interfaces abstractas regulando adaptadores (Puertos).
    │   └── helpers/            # Calculadores e identificadores numéricos y de fechas puros.
    ├── application/            # Casos de uso de negocio (Use Cases).
    │   └── get_resources_use_case.py
    └── infrastructure/         # Adaptadores (Entrada y Salida).
        ├── config.py           # Centralizador de Pydantic Settings & Env Vars.
        ├── container.py        # Inyector de Dependencias (DI Container Singleton).
        ├── fastapi_app.py      # Levantamiento de Lifespans, Middleware de CORS, Seguridad.
        ├── adapters/           # Adaptadores de tecnologías externas (Redis, Mock DB).
        │   ├── redis_cache_adapter.py
        │   ├── redis_rate_limiter_adapter.py
        │   └── mock_db_repository_adapter.py
        └── http/               # Capa de API Controllers y Rutas.
            ├── routes.py       # Definición e interfaz web de las rutas de FastAPI.
            └── controllers/    # Controladores que mapean y procesan las solicitudes.
                └── resources_controller.py  # Controlador HTTP que delega a los casos de uso.
```

---

## ⚙️ Entornos de Ejecución (Desarrollo vs Producción)

El proyecto ofrece un comportamiento diferenciado según el entorno establecido por la variable `ENVIRONMENT`:

### 🛠️ Entorno de Desarrollo (`ENVIRONMENT=development`)
Orientado a agilizar la rapidez del desarrollo y pruebas rápidas:
1. **Bypass de API Key / Seguridad Laxa**: Los endpoints protegidos permiten el acceso con cualquier API Key o cabecera ausente, logueando un aviso de bypass local sin bloquear las solicitudes.
2. **Hot-Reload Automático**: Al arrancar `app.py` de forma manual o con docker, los cambios se recargan al instante en caliente.
3. **Mocks y Fallback del Almacenamiento**: Si Redis no está disponible o no se puede conectar, la API arranca con un cliente mock en memoria (`MockRedisClient`) sin caídas de servicio.

### 🚀 Entorno de Producción (`ENVIRONMENT=production`)
Fijado para despliegues de grado de producción:
1. **Validación Estricta de API Key**: Bloqueo estricto del tráfico anónimo y denegaciones `401 Unauthorized` / `403 Forbidden`.
2. **Worker de Caché Distribuido con Autolock**: Sincronización precisa y background loop a través de locks distribuidos en Redis.
3. **Hot-Reload Deshabilitado**: Optimización máxima de hilos y sockets.

---

## 🧰 Versiones Recomendadas

Para evitar errores de entorno y diferencias entre máquinas, use estas versiones base:

- **Python**: `3.13.x` recomendado. Mínimo práctico para este proyecto: `3.11+`.
- **pip**: `24+` recomendado.
- **virtualenv / venv**: usar el módulo nativo `python -m venv`.
- **Redis Server**: `7.x` recomendado si desea ejecutar caché/rate-limit real. Si `USE_REDIS=False`, Redis no es obligatorio en desarrollo.
- **Docker Engine**: `24+` recomendado.
- **Docker Compose**: `v2.20+` recomendado.
- **Git**: `2.40+` recomendado.

Dependencias Python del proyecto:

- **FastAPI**: `>=0.110.0`
- **Uvicorn**: `>=0.28.0`
- **Pydantic**: `>=2.6.0`
- **pydantic-settings**: `>=2.2.0`
- **redis-py**: `>=5.0.0`
- **pytest**: `>=8.0.0`
- **httpx**: `>=0.27.0`

Si va a desplegar en Vercel, use la versión más reciente de la CLI de Vercel y mantenga `requirements.txt` como fuente principal de dependencias.

---

## 🚀 Guía de Levantamiento de la Aplicación

### Paso 1: Instalar Dependencias Locales (Opcional si usa Docker)
Crear un entorno virtual de Python y arrancar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Importante:
- Si ejecutas `python app.py` sin activar el entorno virtual, es normal que falle con errores como `ModuleNotFoundError: No module named 'uvicorn'`.
- En Windows puedes arrancar directamente con `.\.venv\Scripts\python.exe app.py`.
- En Linux o macOS puedes arrancar directamente con `./.venv/bin/python app.py`.

### Paso 2: Configurar su entorno
Para desarrollo local, copie `.env.dev` o configure la variable `ENVIRONMENT=development` en su archivo `.env`:
```bash
cp .env.dev .env
```

### Paso 3: Arrancar localmente sin Docker
Con el entorno virtual ya activo, o usando el ejecutable del `.venv`, inicie la API:
```bash
python app.py
```

### Paso 4: Arrancar con Docker Compose (Recomendado)
Levanta de manera automática la API funcional y el servidor Redis de caché en contenedores independientes:
```bash
docker-compose up --build -d
```
La aplicación se encontrará lista en `http://localhost:8000`.

---

## 🛠️ Pruebas Locales Manuales durante el Desarrollo

Durante el desarrollo, no necesitas configurar Redis ni API Keys válidas en cada petición gracias al **Modo Desarrollo**. Aquí tienes una guía rápida de cómo probar tu API de inmediato:

### 1. Probar sin Redis (Auto-Mock)
Si ejecutas la API localmente (`python app.py`) y no tienes un servidor Redis corriendo, la aplicación usará directamente el modo mock cuando `USE_REDIS=False`, o activará el failover automático si Redis está habilitado pero no responde.
- La API seguirá funcionando perfectamente.
- Los límites de peticiones (Rate Limit) registrarán logs pero no bloquearán tus consultas.

### 2. Probar Endpoints Autenticados
Normalmente los endpoints bajo `/api/v1/...` requieren la cabecera `X-API-Key` y validación robusta. Sin embargo, en desarrollo:
- Puedes enviar peticiones **sin cabecera** o con cualquier valor arbitrario (ej. `X-API-Key: lala`).
- El backend los validará de manera laxa, registrará un aviso en la terminal `[BYPASS] API-Key checking bypassed under development mode` y te dará acceso sin problemas.

#### Ejemplo de Petición con cURL:
```bash
curl -X GET "http://localhost:8000/api/v1/resources" \
  -H "X-API-Key: desarrollo"
```

#### Ejemplo de Petición con Python `requests`:
```python
import requests

headers = {"X-API-Key": "cualquier_cosa_en_desarrollo"}
response = requests.get("http://localhost:8000/api/v1/resources", headers=headers)
print(response.json())
```


---

## 🔒 Consumo Seguro de Endpoints

### 1. Validación de Salud (Health Probe)
- **Ruta**: `GET http://localhost:8000/`
- **Autenticación**: Ninguna (Público).

### 2. Obtener Recursos (Endpoint Protegido)
- **Ruta**: `GET http://localhost:8000/api/v1/resources`
- **Autenticación**: Requiere la cabecera `X-API-Key` provista en su archivo `.env` (Excepto en `ENVIRONMENT=development`).
- **Rate-limit**: Protegido con **20 peticiones por minuto** para prevenir sobreingestas.

---

## 🧪 Ejecución de Pruebas de Software
Para arrancar las suites de testeo unitarias y comprobar la integridad funcional de forma automatizada, use:
```bash
pytest
```
