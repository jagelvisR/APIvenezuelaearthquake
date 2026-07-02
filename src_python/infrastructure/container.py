import logging
import redis
from .adapters.redis_cache_adapter import RedisCacheAdapter
from .adapters.redis_rate_limiter_adapter import RedisRateLimiterAdapter
from .adapters.mock_db_repository_adapter import MockDBRepositoryAdapter
from .adapters.mock_emergency_zone_repository_adapter import MockEmergencyZoneRepositoryAdapter
from ..application.get_resources_use_case import GetResourcesUseCase
from ..application.emergency_use_case import EmergencyUseCase
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
        self.cache_service, self.rate_limiter = self._build_resilience_services()
        self.resource_repository, self.emergency_zone_repository = self._build_repositories()
        self.get_resources_use_case, self.emergency_use_case = self._build_use_cases()

    def _build_resilience_services(self):
        # Resuelve caché y rate limit una sola vez al boot.
        # Si Redis está desactivado, evita cualquier ping y usa fallback local desde el inicio.
        if not getattr(settings, "USE_REDIS", True):
            logger.info("ℹ️ Redis se encuentra desactivado bajo el flag USE_REDIS. Usando Adaptadores InMemory.")
            return RedisCacheAdapter(enabled=False), RedisRateLimiterAdapter(enabled=False)

        if self._redis_available():
            logger.info("📡 Conexión a Redis exitosa. Usando adaptadores de producción Redis.")
            return RedisCacheAdapter(), RedisRateLimiterAdapter()

        return RedisCacheAdapter(), RedisRateLimiterAdapter()

    def _redis_available(self) -> bool:
        try:
            test_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_connect_timeout=1.5,
            )
            test_client.ping()
            return True
        except Exception as error:
            logger.warning(
                f"⚠️ Servidor Redis no se pudo conectar en {settings.REDIS_HOST}:{settings.REDIS_PORT} ({error}). Usando Fallback InMemory."
            )
            return False

    def _build_repositories(self):
        # Los repositorios actuales son mock; DATABASE_URL queda reservada para una implementación futura.
        return MockDBRepositoryAdapter(), MockEmergencyZoneRepositoryAdapter()

    def _build_use_cases(self):
        # Los casos de uso sólo reciben puertos ya resueltos por el contenedor.
        resources_use_case = GetResourcesUseCase(
            repository=self.resource_repository,
            cache_service=self.cache_service,
        )
        emergency_use_case = EmergencyUseCase(
            repository=self.emergency_zone_repository,
        )
        return resources_use_case, emergency_use_case

# Instanciación única global (Singleton)
container = Container()
