# Documentación Técnica: Arquitectura Hexagonal y Flujo de Peticiones

Este documento detalla la estructura arquitectónica, el flujo de ejecución de peticiones y los mecanismos de contingencia (failover) implementados en la API.

---

## 1. Estructura de la Arquitectura Hexagonal

Esta aplicación utiliza la **Arquitectura Hexagonal (Puertos y Adaptadores)** para aislar la lógica del negocio de los detalles tecnológicos e infraestructura externa (como frameworks web, bases de datos o sistemas de caché).

```mermaid
graph TD
    %% Infraestructura Externa (Lado Entrada)
    HTTPCli[Cliente HTTP] -->|Petición API| APIController[HTTP Controller]
    
    subgraph Capa_Infraestructura [Capa de Infraestructura]
        APIController
        RedisCache[RedisCacheAdapter]
        RedisRate[RedisRateLimiterAdapter]
        MockDB[MockDBRepositoryAdapter]
    end

    %% Puertos / Interfaces
    subgraph Capa_Dominio [Capa de Dominio]
        direction TB
        models[Modelos de Entidad]
        
        subgraph Puertos [Puertos / Interfaces]
            ICache[ICacheService]
            IRate[IRateLimiter]
            IRepo[IResourceRepository]
        end
    end

    %% Casos de Uso
    subgraph Capa_Aplicacion [Capa de Aplicación]
        UseCase[GetResourcesUseCase]
    end

    %% Relaciones / Sentido de las Dependencias
    APIController -->|1. Invoca| UseCase
    UseCase -->|2. Orquesta mediante| ICache
    UseCase -->|3. Consulta mediante| IRepo
    
    %% Implementaciones de Puertos
    RedisCache -.->|Implementa| ICache
    RedisRate -.->|Implementa| IRate
    MockDB -.->|Implementa| IRepo

    classDef Capa_Infraestructura fill:#f9f,stroke:#333,stroke-width:2px;
    classDef Capa_Dominio fill:#bbf,stroke:#333,stroke-width:2px;
    classDef Capa_Aplicacion fill:#bfb,stroke:#333,stroke-width:2px;
```

### Capas:
1. **Dominio (Núcleo Puro):** Define las reglas del negocio, entidades ([models.py](src_python/domain/models.py)) y los contratos que regulan la salida/entrada de datos ([repository_ports.py](src_python/domain/repository_ports.py)). No tiene dependencias de librerías externas.
2. **Aplicación (Casos de Uso):** Contiene la lógica orquestadora específica de cada acción ([get_resources_use_case.py](src_python/application/get_resources_use_case.py)). Consume los puertos del dominio.
3. **Infraestructura (Adaptadores):** Implementa los puertos definidos en el Dominio. Aquí interactuamos con bases de datos, Redis para caché y librerías web como FastAPI.

---

## 2. Flujo de una Petición (Request Flow)

Cuando un cliente hace una llamada GET al endpoint `/api/v1/resources`, se desencadena la siguiente secuencia:

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as Cliente HTTP
    participant App as fastapi_app (Router)
    participant Rate as RedisRateLimiterAdapter
    participant UseCase as GetResourcesUseCase
    participant Cache as RedisCacheAdapter
    participant DB as MockDBRepositoryAdapter

    Cliente ->> App: GET /api/v1/resources
    Note over App: Aplica Middleware y valida API-Key
    App ->> Rate: is_allowed(client_ip)
    
    alt Límite Excedido (Rate Limit)
        Rate -->> App: Retorna False
        App -->> Cliente: 429 Too Many Requests
    else Tráfico Permitido
        Rate -->> App: Retorna True
        App ->> UseCase: execute(category, refresh)
        
        alt Consulta con Caché Activa (Default)
            UseCase ->> Cache: get(cache_key)
            alt Clave en Caché encontrada
                Cache -->> UseCase: Datos (JSON)
                UseCase -->> App: Retorna Recursos
                App -->> Cliente: 200 OK (Caché hit)
            else Clave no encontrada (Cache Miss)
                Cache -->> UseCase: None
                UseCase ->> DB: fetch_all(category)
                DB -->> UseCase: Modelos de Entidad Frescos
                UseCase ->> Cache: set(cache_key, serializados)
                UseCase -->> App: Retorna Recursos
                App -->> Cliente: 200 OK (Fresh Load)
            end
        else Consulta Forzada (refresh=True)
            UseCase ->> DB: fetch_all(category)
            DB -->> UseCase: Modelos de Entidad Frescos
            UseCase ->> Cache: set(cache_key, serializados)
            UseCase -->> App: Retorna Recursos
            App -->> Cliente: 200 OK (Fresh Override)
        end
    end
```

### Detalle del Flujo de Ejecución:
1. **Entrada y Seguridad:** La petición pasa por [fastapi_app.py](src_python/infrastructure/fastapi_app.py) para evaluar excepciones generales, CORS y verificar cabeceras del token de autenticación.
2. **Rate Limiting:** El router de la API ([fastapi_controller.py](src_python/infrastructure/http/fastapi_controller.py)) llama a `is_allowed()` del adaptador `RedisRateLimiterAdapter`.
3. **Caso de Uso:** Si se aprueba, se delega al caso de uso `GetResourcesUseCase`.
4. **Caché Térmica:** Éste valida si el recurso consultado ya se encuentra serializado en el servicio de caché:
   - **Caso Positivo:** Retorna los datos inmediatamente, evitando consultas costosas.
   - **Caso Negativo:** Consulta el repositorio de datos de infraestructura (`MockDBRepositoryAdapter`), actualiza la caché para futuras consultas y finalmente retorna los datos al controller.

---

## 3. Comportamiento en Modo Failover (Redis Caído o Desactivado)

Una particularidad del diseño es que la aplicación **nunca se interrumpe** si Redis se apaga o si se desactiva en el archivo `.env` (`USE_REDIS=False`). 

Esto se gestiona a través del contenedor de Inyección de Dependencias en [container.py](src_python/infrastructure/container.py):

```mermaid
graph TD
    Start[Contenedor Inicializa] --> CheckEnv{¿USE_REDIS == True?}
    
    CheckEnv -->|Sí| TestConn{¿Ping a Redis Exitoso?}
    CheckEnv -->|No| Fallback[Carga Clientes Mock e Inicia en Memoria Local]
    
    TestConn -->|Sí| ProdAdapters[Vincula adaptadores nativos de Redis]
    TestConn -->|No| Fallback
    
    Fallback --> MockCache[RedisCacheAdapter -> Inicializa MockRedisClient]
    Fallback --> MockRate[RedisRateLimiterAdapter -> Desactiva límite con un Fail-safe]
```

### Lógica de Recuperación Dinámica:
* **Adaptador de Caché en Memoria:** Ante un timeout en la conexión durante el inicio o ciclo de ejecución, [redis_cache_adapter.py](src_python/infrastructure/adapters/redis_cache_adapter.py) atrapa la excepción `redis.TimeoutError` o `redis.ConnectionError` y sustituye dinámicamente la instancia del cliente `redis.Redis` por un diccionario interno `MockRedisClient` almacenado en memoria RAM local.
* **Adaptador de Rate Limiting Tolerante a Fallos:** Ante caídas de conexión, [redis_rate_limiter_adapter.py](src_python/infrastructure/adapters/redis_rate_limiter_adapter.py) inhabilita internamente el bloqueo de tráfico convirtiéndose en un passthrough permisivo (`_available = False`), garantizando que la API continúe respondiendo peticiones legítimas de forma ininterrumpida.
