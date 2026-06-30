# Backend API - APIVENEZUELAEARTHQUAKE

Backend FastAPI con Arquitectura Hexagonal para dos slices funcionales actuales:

- `resources`: catálogo de recursos con caché y rate limit.
- `emergency`: zonas de emergencia, necesidades, fuentes y resumen operacional.

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
│   │   ├── emergency_use_case.py
│   │   └── get_resources_use_case.py
│   ├── domain/
│   │   ├── emergency_models.py
│   │   ├── emergency_repository_ports.py
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
│       │   ├── mock_emergency_zone_repository_adapter.py
│       │   ├── redis_cache_adapter.py
│       │   └── redis_rate_limiter_adapter.py
│       └── http/
│           ├── emergency_routes.py
│           ├── routes.py
│           ├── rate_limiter_decorator.py
│           ├── controllers/
│           │   ├── emergency_controller.py
│           │   └── resources_controller.py
│           └── schemas/
│               └── emergency_schemas.py
└── tests/
    ├── test_api_core.py
    └── test_emergency.py
```

## Endpoints Disponibles

### Resources

- `GET /api/v1/status`
- `GET /api/v1/resources`
- `POST /api/v1/resources/parse-value`

Parámetros de `GET /api/v1/resources`:

- `category`: filtra por categoría exacta.
- `refresh`: si vale `true`, fuerza lectura fresca y reescritura de caché.

### Emergency

- `GET /api/v1/emergency/zones`
- `GET /api/v1/emergency/zones/{zone_id}`
- `POST /api/v1/emergency/zones`
- `PATCH /api/v1/emergency/zones/{zone_id}/status`
- `GET /api/v1/emergency/needs`
- `GET /api/v1/emergency/sources`
- `GET /api/v1/emergency/summary`

Filtros de `GET /api/v1/emergency/zones`:

- `state`
- `municipality`
- `status`
- `attended`
- `need`

### Documentación Protegida Con Basic Auth

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

## Guía De Levantamiento

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

Importante:

- Si ejecutas `python app.py` sin activar el entorno virtual, puede fallar por dependencias ausentes.
- En Windows puedes arrancar directamente con `./.venv/Scripts/python.exe app.py`.

### Opción 2: Docker Compose

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

- Todas las rutas montadas bajo `/api` requieren `X-API-Key` en producción.
- `GET /api/v1/status` también cae bajo ese prefijo, así que en producción no es pública.
- `/docs` y `/redoc` usan autenticación Basic.

## Redis, Caché Y Rate Limit

- `GET /api/v1/resources` usa el decorador de rate limit definido en [src_python/infrastructure/http/rate_limiter_decorator.py](src_python/infrastructure/http/rate_limiter_decorator.py).
- El límite actual es `20` peticiones por `60` segundos por IP y nombre de función.
- La caché de recursos usa claves del tipo `resources:list:<category>`.
- Cuando Redis no está disponible, la caché se sustituye por `MockRedisClient` en memoria y el rate limit pasa a modo permisivo.

## Ejemplos De Uso

### Health check

```bash
curl -X GET "http://localhost:8000/api/v1/status" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

```json
{
  "status": "healthy",
  "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
  "version": "1.0.0"
}
```

### Listar recursos

```bash
curl -X GET "http://localhost:8000/api/v1/resources" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

### Filtrar recursos por categoría

```bash
curl -G "http://localhost:8000/api/v1/resources" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  --data-urlencode "category=IA"
```

### Parsear valor financiero

```bash
curl -X POST "http://localhost:8000/api/v1/resources/parse-value" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  -d '{"value":"1.250,75","fecha":"2026-06-30"}'
```

### Listar zonas de emergencia

```bash
curl -X GET "http://localhost:8000/api/v1/emergency/zones" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

### Filtrar zonas por estado y necesidad

```bash
curl -G "http://localhost:8000/api/v1/emergency/zones" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  --data-urlencode "state=Lara" \
  --data-urlencode "need=agua"
```

### Crear zona de emergencia

```bash
curl -X POST "http://localhost:8000/api/v1/emergency/zones" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  -d '{"state":"Táchira","municipality":"San Cristóbal","description":"Zona con necesidad de refugio temporal reportada por operadores.","needs":["refugio"],"source_name":"Formulario manual","source_type":"manual"}'
```

### Actualizar estado de zona

```bash
curl -X PATCH "http://localhost:8000/api/v1/emergency/zones/zone_02/status" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
  -d '{"status":"attended"}'
```

### Respuestas típicas de error

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

Con necesidad inválida al crear una zona:

```json
{
  "detail": "Necesidad 'internet' no reconocida. Valores permitidos: agua, comida, medicinas, ropa, refugio, transporte, atención médica, maquinaria, voluntarios"
}
```

## Pruebas

Suites actuales:

- `tests/test_api_core.py`
- `tests/test_emergency.py`

Ejecutar todo:

```bash
pytest tests/test_api_core.py tests/test_emergency.py
```

Cobertura funcional actual:

- parsing financiero;
- `GetResourcesUseCase`;
- `EmergencyUseCase`;
- endpoints HTTP de `resources` y `emergency`.
