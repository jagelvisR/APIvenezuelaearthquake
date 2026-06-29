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

## 🚀 Guía de Levantamiento de la Aplicación

### Paso 1: Instalar Dependencias Locales (Opcional si usa Docker)
Crear un entorno virtual de Python y arrancar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Paso 2: Configurar su entorno
Para desarrollo local, copie `.env.dev` o configure la variable `ENVIRONMENT=development` en su archivo `.env`:
```bash
cp .env.dev .env
```

### Paso 3: Arrancar con Docker Compose (Recomendado)
Levanta de manera automática la API funcional y el servidor Redis de caché en contenedores independientes:
```bash
docker-compose up --build -d
```
La aplicación se encontrará lista en `http://localhost:8000`.

---

## 🛠️ Pruebas Locales Manuales durante el Desarrollo

Durante el desarrollo, no necesitas configurar Redis ni API Keys válidas en cada petición gracias al **Modo Desarrollo**. Aquí tienes una guía rápida de cómo probar tu API de inmediato:

### 1. Probar sin Redis (Auto-Mock)
Si ejecutas la API localmente (`python app.py`) y no tienes un servidor Redis corriendo, la aplicación detectará el fallo de conexión automáticamente o la variable `ENVIRONMENT=development` y activará el **`MockRedisClient`**.
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

---

## 🆘 Emergency endpoints (MVP mock/in-memory)

> **Nota:** Esta primera versión del módulo Emergency usa **datos mock en memoria**. Los reportes **no son persistentes** y se pierden al reiniciar el proceso. No almacena datos personales sensibles (nombre, cédula, teléfono ni dirección exacta).

Endpoints bajo el prefijo `/api/v1/emergency` (tag **Emergency** en Swagger):

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/zones` | Lista zonas reportadas (filtros: `state`, `municipality`, `status`, `attended`, `need`) |
| `GET` | `/zones/{zone_id}` | Detalle de una zona |
| `POST` | `/zones` | Crea un reporte de zona en memoria |
| `PATCH` | `/zones/{zone_id}/status` | Actualiza el estado operativo |
| `GET` | `/needs` | Resumen de necesidades agrupadas |
| `GET` | `/sources` | Fuentes de información registradas |
| `GET` | `/summary` | Resumen general (totales, necesidades críticas, zonas por estado) |

**Estados permitidos:** `reported`, `needs_attention`, `in_progress`, `attended`, `resolved`

**Necesidades reconocidas:** `agua`, `comida`, `medicinas`, `ropa`, `refugio`, `transporte`, `atención médica`, `maquinaria`, `voluntarios`

### Ejemplos con cURL

Listar zonas que necesitan agua en Lara:
```bash
curl "http://localhost:8000/api/v1/emergency/zones?state=Lara&need=agua"
```

Ver detalle de una zona:
```bash
curl "http://localhost:8000/api/v1/emergency/zones/zone_01"
```

Crear un reporte de zona (sin datos personales):
```bash
curl -X POST "http://localhost:8000/api/v1/emergency/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "Carabobo",
    "municipality": "Valencia",
    "sector": "Zona industrial",
    "description": "Comunidad sin acceso a agua potable. Sin dirección exacta.",
    "needs": ["agua", "transporte"],
    "status": "reported",
    "attended": false,
    "source_name": "Discord - Coordinación Voluntarios VE",
    "source_type": "discord"
  }'
```

Actualizar estado de una zona:
```bash
curl -X PATCH "http://localhost:8000/api/v1/emergency/zones/zone_03/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

Resumen de necesidades y panorama general:
```bash
curl "http://localhost:8000/api/v1/emergency/needs"
curl "http://localhost:8000/api/v1/emergency/sources"
curl "http://localhost:8000/api/v1/emergency/summary"
```

Documentación interactiva (usuario `admin`, contraseña `admin123`): `http://localhost:8000/docs`
