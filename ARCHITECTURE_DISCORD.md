# 📐 INFRAESTRUCTURA Y FLUJO DE LA API (Hexagonal)

Este documento contiene la explicación de la arquitectura y flujos de ejecución optimizados para una lectura limpia desde **Discord**.

---

## 1. Mapa de la Arquitectura Hexagonal

En Discord, donde no se renderizan diagramas dinámicos, podemos visualizar la estructura de **Puertos y Adaptadores** de la siguiente manera:

```
[ CAPA DE INFRAESTRUCTURA (Detalles Técnicos) ]
   │
   ├── Adaptadores de Entrada:
   │     └── [ Cliente HTTP ] ──► ( Petición ) ──► [ HTTP Controller (FastAPI) ]
   │                                                     │
   │   ┌─────────────────────────────────────────────────┘
   │   ▼
[ CAPA DE APLICACIÓN (Casos de Uso) ]
   │
   └── [ GetResourcesUseCase (Caso de Uso Principal) ]
         │
         ├───► usa el Puerto ──► [ ICacheService ]     ──► [ RedisCacheAdapter ] (Mock en memoria si falla)
         ├───► usa el Puerto ──► [ IResourceRepository ] ──► [ MockDBRepositoryAdapter ]
         └───► usa el Puerto ──► [ IRateLimiter ]      ──► [ RedisRateLimiterAdapter ] (Fail-safe permisivo si falla)
```

### Resumen de Capas:
* **Dominio (Núcleo Puro):** Define las reglas matemáticas y de negocio puras, entidades (`models.py`) y contratos/interfaces (`repository_ports.py`). No depende de frameworks.
* **Aplicación (Casos de Uso):** Orquesta la lógica del negocio (`get_resources_use_case.py`).
* **Infraestructura (Adaptadores):** Implementa los puertos para hablar con el exterior (Base de Datos, Redis, HTTP).

---

## 2. Flujo de una Petición (Paso a Paso)

Cuando un cliente interactúa con la API, el flujo recorre cada capa de forma segura:

```
CLIENTE                      FASTAPI (App)                   REDIS (Caché)                 BASE DE DATOS
  │                                │                              │                              │
  ├───[1. GET /resources]─────────►│                              │                              │
  │    (Valida API-Key y CORS)     │                              │                              │
  │                                ├───[2. ¿IP Bajo Límite?]─────►│                              │
  │                                │    (Rate Limiter)            │                              │
  │                                │◄──[Retorna Permitido]────────┤                              │
  │                                │                              │                              │
  │                                ├───[3. ¿Existe Caché?]───────►│                              │
  │                                │◄──[No existe (Cache Miss)]───┤                              │
  │                                │                              │                              │
  │                                ├───[4. Buscar Datos]────────────────────────────────────────►│
  │                                │◄──[Envía Recursos]──────────────────────────────────────────┤
  │                                │                              │                              │
  │                                ├───[5. Guardar en Caché]─────►│                              │
  │◄──[6. Retorna 200 OK con JSON]─┤                              │                              │
```

---

## 3. Lógica de Failover Automático (Redis Caído/Desactivado)

Si tu servidor de Redis está apagado o tienes `USE_REDIS=False` en el `.env`, el contenedor de inyección de dependencias (`container.py`) y los adaptadores lo detectan sin interrumpir el servicio:

```
[ Inicialización ] ──► ¿USE_REDIS == True?
                            │
              ┌─────────────┴─────────────┐
              ▼ SÍ                        ▼ NO
       ¿Ping a Redis responde?     ┌────────────────────────┐
        ┌─────┴─────┐              │ ACTIVA MODO FAILOVER   │
     SÍ ▼           ▼ NO           │ (Local Memory Mock)    │
  ┌──────────┐   ┌───────────┐     │  - MockRedisClient     │
  │ Usa      │   │ Activa    │◄────┤  - Fail-safe Permisivo │
  │ Redis    │   │ Failover  │     └────────────────────────┘
  └──────────┘   └───────────┘
```

* **Caché Fallback:** Si se cae Redis, se activa un diccionario (`MockRedisClient`) en la RAM de la propia máquina de forma transparente.
* **Rate-Limit Fallback:** Si la conexión falla, se desactiva el límite temporalmente (`_available = False`) para no bloquear injustamente a los usuarios.
