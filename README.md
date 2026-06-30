# Backend API - APIVENEZUELAEARTHQUAKE

Backend FastAPI con Arquitectura Hexagonal para exponer recursos consultables, parseo financiero auxiliar, caché con Redis opcional y fallback en memoria.

## Resumen

- Framework HTTP: FastAPI.
- Entry point ASGI: `app:app`.
- Prefix global de API: `/api`.
- Versionado actual: `/v1`.
- Seguridad: API key para rutas bajo `/api` y Basic Auth para `/docs` y `/redoc`.
- Caché y rate limit: Redis cuando está disponible; fallback local cuando Redis está desactivado o no responde.
- Puerto: configurable con la variable `PORT`.

## Estructura Real Del Proyecto

```text
apivenezuelaearthquake_backend/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── README.md
├── ARCHITECTURE.md
├── ARCHITECTURE_DISCORD.md
├── requirements.txt
├── .env.example
├── .env.dev
├── src_python/
│   ├── application/
│   │   └── get_resources_use_case.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── repository_ports.py
│   │   └── helpers/
│   │       └── financial_parser_helper.py
│   └── infrastructure/
│       ├── config.py
│       ├── container.py
│       ├── fastapi_app.py
│       ├── adapters/
│       │   ├── mock_db_repository_adapter.py
│       │   ├── redis_cache_adapter.py
│       │   └── redis_rate_limiter_adapter.py
│       └── http/
│           ├── routes.py
│           ├── rate_limiter_decorator.py
│           └── controllers/
│               └── resources_controller.py
└── tests/
    └── test_api_core.py
```

## Endpoints Disponibles

### Público

- `GET /api/v1/status`
  Devuelve estado simple de salud y versión.

### Protegidos con `X-API-Key`

- `GET /api/v1/resources`
  Lista recursos desde caché o repositorio mock.

Parámetros:

- `category`: filtra por categoría exacta.
- `refresh`: si vale `true`, fuerza lectura fresca y reescritura de caché.

- `POST /api/v1/resources/parse-value`
  Ejecuta parseo auxiliar de valores numéricos y fecha.

Payload de ejemplo:

```json
{
  "value": "1.250,75",
  "fecha": "2026-06-30"
}
```

Respuesta de ejemplo:

```json
{
  "original": "1.250,75",
  "parsed_float": 1250.75,
  "parsed_int": 1250,
  "parsed_fecha": "2026-06-30T00:00:00"
}
```

### Documentación Protegida con Basic Auth

- `GET /docs`
- `GET /redoc`

Credenciales por defecto en desarrollo según `.env.dev`:

- Usuario: `admin`
- Password: `admin123`

## Variables De Entorno

Definidas en [src_python/infrastructure/config.py](src_python/infrastructure/config.py).

| Variable | Default | Uso |
|---|---|---|
| `ENVIRONMENT` | `production` | Activa comportamiento de desarrollo o producción |
| `PORT` | `8000` | Puerto HTTP usado por Uvicorn |
| `REDIS_HOST` | `localhost` | Host de Redis |
| `REDIS_PORT` | `6379` | Puerto de Redis |
| `REDIS_CACHE_DB` | `0` | Base Redis para caché |
| `REDIS_RATE_LIMIT_DB` | `1` | Base Redis para rate limit |
| `USE_REDIS` | `True` | Habilita Redis nativo o fallback local |
| `DATABASE_URL` | `""` | Reservada para persistencia futura |
| `API_KEY` | valor por defecto interno | API key para rutas protegidas |
| `CORS_ORIGINS` | `*` | Lista separada por comas |
| `SWAGGER_USERNAME` | `admin` | Usuario de docs |
| `SWAGGER_PASSWORD` | `admin123` | Password de docs |

## Modos De Ejecución

### Desarrollo

Con `ENVIRONMENT=development`:

- `app.py` arranca Uvicorn con `reload=True`.
- La validación de `X-API-Key` permite bypass local.
- El worker proactivo no se inicia.
- Si `USE_REDIS=False`, el contenedor usa directamente fallback en memoria sin intentar `ping()` a Redis.

### Producción

Con `ENVIRONMENT=production`:

- `reload=False`.
- La API key se valida estrictamente.
- El worker proactivo puede refrescar caché en background.
- Si `USE_REDIS=True`, la app intenta usar Redis real y cae a fallback sólo si la conexión falla.

## Levantar El Proyecto Localmente

### Opción 1: Python local

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
copy .env.dev .env
```

```bash
python app.py
```

La API quedará escuchando en `http://localhost:<PORT>`.

### Opción 2: Docker Compose

El compose ya soporta puertos distintos por entorno.

Linux/macOS:

```bash
PORT=8081 docker compose up --build
```

PowerShell:

```powershell
$env:PORT=8081
docker compose up --build
```

Si no defines `PORT`, se usa `8000`.

## Seguridad

- Todas las rutas incluidas bajo `app.include_router(..., prefix="/api", dependencies=[Security(validate_api_key)])` requieren `X-API-Key`.
- `GET /api/v1/status` también cae bajo ese prefijo, pero en desarrollo admite bypass por diseño.
- `/docs` y `/redoc` no son públicas; usan autenticación Basic.

Ejemplo con cURL:

```bash
curl -X GET "http://localhost:8000/api/v1/resources" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

## Ejemplos De Uso

### 1. Health check

Request:

```bash
curl -X GET "http://localhost:8000/api/v1/status" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

Response:

```json
{
  "status": "healthy",
  "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
  "version": "1.0.0"
}
```

### 2. Listar recursos

Request:

```bash
curl -X GET "http://localhost:8000/api/v1/resources" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

Response:

```json
[
  {
    "id": "res_01",
    "name": "Servicio de Autenticación Central",
    "description": "Clúster SSO integrado con soporte JWT.",
    "category": "Sistemas",
    "created_at": "2026-06-30T10:00:00",
    "properties": {
      "sla": "99.99%",
      "owner": "DevOps Team"
    }
  }
]
```

El arreglo real contiene más de un recurso; el ejemplo está acotado al formato de respuesta.

### 3. Filtrar por categoría

Request:

```bash
curl -G "http://localhost:8000/api/v1/resources" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  --data-urlencode "category=IA"
```

Response esperada:

```json
[
  {
    "id": "res_02",
    "name": "Motor de Predicciones AI",
    "description": "Servicio conversacional de inferencia inteligente.",
    "category": "IA",
    "created_at": "2026-06-30T10:00:00",
    "properties": {
      "model": "deepseek-reasoner",
      "api_calls_quota": 5000
    }
  }
]
```

### 4. Forzar refresh de caché

Request:

```bash
curl -G "http://localhost:8000/api/v1/resources" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  --data-urlencode "refresh=true"
```

Efecto:

- omite la lectura de caché para esa llamada;
- vuelve a consultar el repositorio mock;
- reescribe la clave de caché correspondiente.

### 5. Parsear valor financiero

Request:

```bash
curl -X POST "http://localhost:8000/api/v1/resources/parse-value" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  -d '{"value":"1.250,75","fecha":"2026-06-30"}'
```

Response:

```json
{
  "original": "1.250,75",
  "parsed_float": 1250.75,
  "parsed_int": 1250,
  "parsed_fecha": "2026-06-30T00:00:00"
}
```

### 6. Abrir Swagger protegido

Request:

```bash
curl -u admin:admin123 "http://localhost:8000/docs"
```

### 7. Respuestas típicas de autenticación

Sin API key en producción:

```json
{
  "detail": "Falta la API Key en el encabezado 'X-API-Key' para autenticación."
}
```

Con API key inválida en producción:

```json
{
  "detail": "La API Key proporcionada es inválida o no cuenta con suficientes permisos."
}
```

Con límite excedido:

```json
{
  "detail": "Has excedido el límite de 20 peticiones por 60 segundos."
}
```

## Redis, Caché Y Rate Limit

- `GET /api/v1/resources` usa el decorador de rate limit definido en `rate_limiter_decorator.py`.
- El límite actual es `20` peticiones por `60` segundos por IP y nombre de función.
- La caché de recursos usa claves del tipo `resources:list:<category>`.
- Cuando Redis no está disponible, la caché se sustituye por `MockRedisClient` en memoria y el rate limit pasa a modo permisivo.

## Pruebas

La suite presente hoy en el repo es:

- `tests/test_api_core.py`

Ejecutar:

```bash
pytest tests/test_api_core.py
```

Cobertura actual de esa suite:

- `FinancialParserHelper.parse_float()`
- `FinancialParserHelper.parse_int()`
- `GetResourcesUseCase.execute()`

## Notas Operativas

- El `Dockerfile` expone `8000`, pero el proceso escucha en el valor de `PORT`.
- El módulo raíz [app.py](app.py) exporta `app`, por lo que sirve tanto para `python app.py` como para `uvicorn app:app`.
- `DATABASE_URL` aún no se usa en el código actual.
