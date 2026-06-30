# 📐 INFRAESTRUCTURA Y FLUJO DE LA API

Versión resumida y alineada con el estado actual del repositorio.

## 1. Mapa De Capas

```text
[ INFRAESTRUCTURA ]
   Cliente HTTP
         │
         └──> FastAPI
                   │
                   ├──> validate_api_key
                   ├──> validate_swagger_auth
                   ├──> rate_limit(...)
                   ├──> ResourcesController
                   │         │
                   │         └──> GetResourcesUseCase
                   │                    │
                   │                    ├──> ICacheService ------> RedisCacheAdapter / MockRedisClient
                   │                    └──> IResourceRepository -> MockDBRepositoryAdapter
                   │
                   └──> EmergencyController
                             │
                             └──> EmergencyUseCase
                                       │
                                       └──> IEmergencyZoneRepository -> MockEmergencyZoneRepositoryAdapter

[ DOMINIO ]
   ResourceModel
   RequestPayload
   ICacheService
   IRateLimiter
   IResourceRepository
   FinancialParserHelper
```

## 2. Endpoints Reales

```text
GET  /api/v1/status
GET  /api/v1/resources
POST /api/v1/resources/parse-value
GET  /api/v1/emergency/zones
GET  /api/v1/emergency/zones/{zone_id}
POST /api/v1/emergency/zones
PATCH /api/v1/emergency/zones/{zone_id}/status
GET  /api/v1/emergency/needs
GET  /api/v1/emergency/sources
GET  /api/v1/emergency/summary
GET  /docs
GET  /redoc
```

Notas:

- Todo lo que cuelga de `/api` usa API key.
- `/docs` y `/redoc` usan Basic Auth.
- No existe un endpoint raíz `GET /` en el estado actual del código.

## 3. Flujo De `GET /api/v1/resources`

```text
1. Entra la request a FastAPI.
2. Se valida X-API-Key.
3. Se ejecuta el decorador de rate limit.
4. ResourcesController delega en GetResourcesUseCase.
5. El caso de uso intenta leer caché usando la clave resources:list:<category>.
6. Si hay caché, responde desde allí.
7. Si no hay caché o refresh=true, consulta MockDBRepositoryAdapter.
8. Serializa el resultado y vuelve a escribir caché.
9. Retorna JSON al cliente.
```

## 4. Flujo De `GET /api/v1/emergency/zones`

```text
1. Entra la request a FastAPI.
2. Se valida X-API-Key.
3. EmergencyController arma filtros.
4. EmergencyUseCase consulta MockEmergencyZoneRepositoryAdapter.
5. Se serializan las zonas.
6. Retorna JSON al cliente.
```

## 5. Redis Y Failover

```text
Container._initialize()
 ├── Si USE_REDIS=False
 │    ├── RedisCacheAdapter(enabled=False)
 │    └── RedisRateLimiterAdapter(enabled=False)
 │
 └── Si USE_REDIS=True
         ├── Hace ping a Redis
         ├── Si responde: usa adaptadores nativos
         └── Si falla: usa fallback tolerante a fallos
```

Consecuencias:

- La API no depende de Redis para arrancar.
- Sin Redis, la caché pasa a memoria local.
- Sin Redis, el rate limit pasa a modo permisivo.

## 6. Entornos

### Development

- `reload=True`
- bypass de API key
- no arranca worker proactivo

### Production

- `reload=False`
- validación estricta de API key
- puede arrancar worker proactivo

## 7. Puerto

```text
PORT -> settings.PORT -> uvicorn.run(..., port=settings.PORT)
```

En Docker Compose:

```text
${PORT:-8000}:${PORT:-8000}
```

Eso permite levantar el mismo servicio en puertos distintos según entorno sin editar código.

## 8. Ejemplos HTTP

### Health check

```text
GET /api/v1/status
X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance
```

Respuesta:

```json
{
   "status": "healthy",
   "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
   "version": "1.0.0"
}
```

### Listar recursos

```text
GET /api/v1/resources
X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance
```

Respuesta de ejemplo:

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

### Parsear valor financiero

```text
POST /api/v1/resources/parse-value
Content-Type: application/json
X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance

{
   "value": "1.250,75",
   "fecha": "2026-06-30"
}
```

### Listar zonas de emergencia

```text
GET /api/v1/emergency/zones
X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance
```

### Crear zona de emergencia

```text
POST /api/v1/emergency/zones
Content-Type: application/json
X-API-Key: secure_apivenezuelaearthquake_key_v1_high_performance

{
   "state": "Táchira",
   "municipality": "San Cristóbal",
   "description": "Zona con necesidad de refugio temporal reportada por operadores.",
   "needs": ["refugio"],
   "source_name": "Formulario manual",
   "source_type": "manual"
}
```

Respuesta:

```json
{
   "original": "1.250,75",
   "parsed_float": 1250.75,
   "parsed_int": 1250,
   "parsed_fecha": "2026-06-30T00:00:00"
}
```

### Errores típicos

Sin API key en producción:

```json
{
   "detail": "Falta la API Key en el encabezado 'X-API-Key' para autenticación."
}
```

Con límite excedido:

```json
{
   "detail": "Has excedido el límite de 20 peticiones por 60 segundos."
}
```
