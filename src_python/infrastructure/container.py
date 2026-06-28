import logging
import redis
from .adapters.redis_cache_adapter import RedisCacheAdapter
from .adapters.redis_rate_limiter_adapter import RedisRateLimiterAdapter
from .adapters.mock_db_repository_adapter import MockDBRepositoryAdapter
from ..application.get_resources_use_case import GetResourcesUseCase
from .config import settings

logger = logging.getLogger("api.container")

class Container:
    """
    Contenedor de Inyección de Dependencias (DI) de la API.
    Asegura un acoplamiento laxo a lo largo de las capas de negocio e infraestructura.
    Selecciona dinámicamente adaptadores InMemory si Redis está desactivado o caído.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Container, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. Resolver Adaptadores de Caché y Límite de Peticiones (Redis vs Fallback InMemory)
        from .adapters.redis_cache_adapter import RedisCacheAdapter, MockRedisClient
        from .adapters.redis_rate_limiter_adapter import RedisRateLimiterAdapter
        
        use_redis_db = getattr(settings, "USE_REDIS", True)
        if use_redis_db:
             try:
                  # Chequeo veloz de ping
                  test_client = redis.Redis(
                      host=settings.REDIS_HOST,
                      port=settings.REDIS_PORT,
                      socket_connect_timeout=1.5
                  )
                  test_client.ping()
                  logger.info("📡 Conexión a Redis exitosa. Usando adaptadores de producción Redis.")
                  self.cache_service = RedisCacheAdapter()
                  self.rate_limiter = RedisRateLimiterAdapter()
             except Exception as e:
                  logger.warning(f"⚠️ Servidor Redis no se pudo conectar en {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e}). Usando Fallback InMemory.")
                  self.cache_service = RedisCacheAdapter() # Auto fallbacks a MockRedisClient
                  self.rate_limiter = RedisRateLimiterAdapter() # Auto fallbacks a fail-safe
        else:
             logger.info("ℹ️ Redis se encuentra desactivado bajo el flag USE_REDIS. Usando Adaptadores InMemory.")
             self.cache_service = RedisCacheAdapter() # Auto fallbacks a MockRedisClient
             self.rate_limiter = RedisRateLimiterAdapter() # Auto fallbacks a fail-safe

        # 2. Adaptador de Almacenamiento Primario
        self.resource_repository = MockDBRepositoryAdapter()
        
        # 3. Casos de Uso del Negocio
        self.get_resources_use_case = GetResourcesUseCase(
            repository=self.resource_repository,
            cache_service=self.cache_service
        )

# Instanciación única global (Singleton)
container = Container()
