# Documentación Técnica: Arquitectura Y Flujo Real Del Proyecto

Este documento describe la arquitectura actual del backend tal como existe hoy en el repositorio: dos slices funcionales, `resources` y `emergency`, expuestos sobre FastAPI con seguridad, caché opcional y fallback local.

## 1. Capas Y Responsabilidades

La aplicación sigue una arquitectura hexagonal mínima.

```mermaid
graph TD
    Client[Cliente HTTP] --> FastAPI[FastAPI Router]
    FastAPI --> ResourceController[ResourcesController]
    FastAPI --> EmergencyController[EmergencyController]
    ResourceController --> UseCase[GetResourcesUseCase]
    EmergencyController --> EmergencyUseCase[EmergencyUseCase]
    UseCase --> CachePort[ICacheService]
    UseCase --> RepoPort[IResourceRepository]
    FastAPI --> RatePort[IRateLimiter]
    EmergencyUseCase --> EmergencyRepoPort[IEmergencyZoneRepository]

    CachePort -.-> RedisCache[RedisCacheAdapter]
    RepoPort -.-> MockRepo[MockDBRepositoryAdapter]
    RatePort -.-> RedisRate[RedisRateLimiterAdapter]
    EmergencyRepoPort -.-> EmergencyMockRepo[MockEmergencyZoneRepositoryAdapter]

    RedisCache --> Redis[(Redis)]
    RedisRate --> Redis
```

### Dominio

- [src_python/domain/models.py](src_python/domain/models.py): modelos de entidad usados por la app.
- [src_python/domain/emergency_models.py](src_python/domain/emergency_models.py): entidades, enums y filtros del módulo emergency.
- [src_python/domain/repository_ports.py](src_python/domain/repository_ports.py): contratos para repositorio, caché y rate limit.
- [src_python/domain/emergency_repository_ports.py](src_python/domain/emergency_repository_ports.py): contrato del repositorio de zonas de emergencia.
- [src_python/domain/helpers/financial_parser_helper.py](src_python/domain/helpers/financial_parser_helper.py): parsing numérico y de fechas.

### Aplicación

- [src_python/application/get_resources_use_case.py](src_python/application/get_resources_use_case.py): caso de uso que obtiene recursos, consulta caché y serializa respuesta.
- [src_python/application/emergency_use_case.py](src_python/application/emergency_use_case.py): casos de uso para zonas, necesidades, fuentes y resumen de emergencia.

### Infraestructura

- [src_python/infrastructure/fastapi_app.py](src_python/infrastructure/fastapi_app.py): instancia FastAPI, CORS, seguridad, docs protegidas y lifespan.
- [src_python/infrastructure/container.py](src_python/infrastructure/container.py): resolución de dependencias y estrategia Redis vs fallback.
- [src_python/infrastructure/adapters/mock_db_repository_adapter.py](src_python/infrastructure/adapters/mock_db_repository_adapter.py): repositorio in-memory actual.
- [src_python/infrastructure/adapters/mock_emergency_zone_repository_adapter.py](src_python/infrastructure/adapters/mock_emergency_zone_repository_adapter.py): repositorio in-memory de zonas de emergencia.
- [src_python/infrastructure/adapters/redis_cache_adapter.py](src_python/infrastructure/adapters/redis_cache_adapter.py): caché Redis con mock local cuando aplica.
- [src_python/infrastructure/adapters/redis_rate_limiter_adapter.py](src_python/infrastructure/adapters/redis_rate_limiter_adapter.py): rate limit Redis con modo permisivo cuando Redis falla o se desactiva.
- [src_python/infrastructure/http/routes.py](src_python/infrastructure/http/routes.py): definición de endpoints.
- [src_python/infrastructure/http/emergency_routes.py](src_python/infrastructure/http/emergency_routes.py): endpoints del módulo emergency.

## 2. Superficie HTTP Actual

La aplicación expone un router principal bajo `/api/v1`, compuesto por endpoints de recursos y de emergencia.

### Endpoints

- `GET /api/v1/status`
- `GET /api/v1/resources`
- `POST /api/v1/resources/parse-value`
- `GET /api/v1/emergency/zones`
- `GET /api/v1/emergency/zones/{zone_id}`
- `POST /api/v1/emergency/zones`
- `PATCH /api/v1/emergency/zones/{zone_id}/status`
- `GET /api/v1/emergency/needs`
- `GET /api/v1/emergency/sources`
- `GET /api/v1/emergency/summary`
- `GET /docs`
- `GET /redoc`

Observación importante:

- Los endpoints bajo `/api` heredan la dependencia global `validate_api_key` configurada en [src_python/infrastructure/fastapi_app.py](src_python/infrastructure/fastapi_app.py).
- `/docs` y `/redoc` usan `validate_swagger_auth` y no se publican como docs abiertas.

## 3. Flujo De `GET /api/v1/resources`

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant App as FastAPI
    participant Rate as RedisRateLimiterAdapter
    participant Controller as ResourcesController
    participant UseCase as GetResourcesUseCase
    participant Cache as RedisCacheAdapter
    participant Repo as MockDBRepositoryAdapter

    Cliente->>App: GET /api/v1/resources
    App->>App: validate_api_key
    App->>Rate: is_allowed(identifier, 20, 60)

    alt rate limit excedido
        Rate-->>App: False
        App-->>Cliente: 429
    else permitido
        Rate-->>App: True
        App->>Controller: get_resources_endpoint(...)
        Controller->>UseCase: execute(category, refresh)

        alt refresh = false y hay caché
            UseCase->>Cache: get(cache_key)
            Cache-->>UseCase: datos serializados
            UseCase-->>Controller: datos
        else refresh = true o no hay caché
            UseCase->>Repo: fetch_all(category)
            Repo-->>UseCase: ResourceModel[]
            UseCase->>Cache: set(cache_key, serialized_data)
            UseCase-->>Controller: datos
        end

        Controller-->>App: JSON
        App-->>Cliente: 200
    end
```

## 4. Flujo De `GET /api/v1/emergency/zones`

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant App as FastAPI
    participant Controller as EmergencyController
    participant UseCase as EmergencyUseCase
    participant Repo as MockEmergencyZoneRepositoryAdapter

    Cliente->>App: GET /api/v1/emergency/zones
    App->>App: validate_api_key
    App->>Controller: list_zones(...)
    Controller->>UseCase: list_zones(filters)
    UseCase->>Repo: fetch_all(filters)
    Repo-->>UseCase: EmergencyZoneModel[]
    UseCase-->>Controller: serialized zones
    Controller-->>App: JSON
    App-->>Cliente: 200
```

## 5. Seguridad

### API Key

Implementada en [src_python/infrastructure/fastapi_app.py](src_python/infrastructure/fastapi_app.py).

- Cabecera: `X-API-Key`
- En `development`: bypass permitido.
- En `production`: cabecera ausente devuelve `401`; valor incorrecto devuelve `403`.

### Basic Auth para documentación

- `GET /docs`
- `GET /redoc`

Comparan usuario y password con `secrets.compare_digest` usando `SWAGGER_USERNAME` y `SWAGGER_PASSWORD`.

## 6. Redis, Fallback Y Arranque

El comportamiento actual del contenedor es el siguiente:

```mermaid
graph TD
    Init[Container._initialize] --> UseRedis{USE_REDIS?}
    UseRedis -->|No| LocalFallback[Instancia adaptadores con enabled=False]
    UseRedis -->|Sí| Ping{Redis responde?}
    Ping -->|Sí| Native[Usa RedisCacheAdapter y RedisRateLimiterAdapter]
    Ping -->|No| Graceful[Usa adaptadores con fallback interno]
```

Detalles reales:

- Si `USE_REDIS=False`, [src_python/infrastructure/container.py](src_python/infrastructure/container.py) evita el `ping()` y crea directamente fallback local.
- Si `USE_REDIS=True` pero Redis no responde, el boot no cae; usa los adaptadores con sus propios mecanismos de contingencia.
- `RedisCacheAdapter(enabled=False)` crea `MockRedisClient` en memoria.
- `RedisRateLimiterAdapter(enabled=False)` queda con `_available = False`, por lo que permite el tráfico.

## 7. Lifespan Y Worker Proactivo

El lifecycle se define en [src_python/infrastructure/fastapi_app.py](src_python/infrastructure/fastapi_app.py).

- En `development` no se crea el worker proactivo.
- En otros entornos se crea `proactive_cache_worker_loop()`.
- Si Redis está desactivado, el worker sigue pudiendo ejecutar refresh directo del caso de uso.

## 8. Configuración De Puerto Y Despliegue

- [src_python/infrastructure/config.py](src_python/infrastructure/config.py) define `PORT`.
- [app.py](app.py) ejecuta Uvicorn usando `settings.PORT`.
- [docker-compose.yml](docker-compose.yml) publica `${PORT:-8000}:${PORT:-8000}`.

Consecuencia:

- El mismo contenedor puede levantarse en distintos puertos sin editar código.

## 9. Limitaciones Actuales Del Proyecto

El repo actual no incluye:

- persistencia real con base de datos;
- integración con fuentes externas reales para zonas de emergencia;
- privacidad avanzada o anonimización persistente más allá del modelo mock.

Lo que sí existe hoy:

- pruebas unitarias del helper financiero y del caso de uso principal;
- pruebas del módulo emergency;
- repositorio mock en memoria;
- endpoints de recursos, parseo y emergencia;
- documentación Swagger/ReDoc protegida.

## 10. Ejemplos HTTP

### Health check

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

### Listar recursos

Request:

```bash
curl -X GET "http://localhost:8000/api/v1/resources" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

Response de ejemplo:

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

### Filtrar por categoría

```bash
curl -G "http://localhost:8000/api/v1/resources" \
    -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance" \
    --data-urlencode "category=IA"
```

### Parsear valor financiero

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

### Listar zonas de emergencia

Request:

```bash
curl -X GET "http://localhost:8000/api/v1/emergency/zones" -H "X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance"
```

### Crear zona de emergencia

Request:

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

### Errores típicos

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
