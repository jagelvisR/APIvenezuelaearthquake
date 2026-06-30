import json
import logging
from typing import Any, Optional
import redis
from ...domain.repository_ports import ICacheService
from ..config import settings

logger = logging.getLogger("api.infrastructure")

class RedisCacheAdapter(ICacheService):
    """Adaptador de Infraestructura para gestión de Caché con Redis."""
    def __init__(self, enabled: bool = True):
        if not enabled:
            self.client = MockRedisClient()
            return

        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_CACHE_DB,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Prueba de ping rápida no bloqueante
            self.client.ping()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"🚨 No se pudo establecer conexión nativa con Redis Server en {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e}). Activando modo failover (Local Memory Mock).")
            self.client = MockRedisClient()

    def get(self, key: str) -> Any:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error al leer de Redis (clave: {key}): {e}")
            return None

    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        try:
            serialized = json.dumps(value)
            self.client.set(key, serialized, ex=timeout)
        except Exception as e:
            logger.error(f"Error al escribir en Redis (clave: {key}): {e}")

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error al eliminar de Redis (clave: {key}): {e}")


class MockRedisClient:
    """Cliente fallback en memoria por si Redis no está levantado."""
    def __init__(self):
        self._store = {}
        
    def ping(self):
        return True
        
    def get(self, key):
        return self._store.get(key)
        
    def set(self, key, value, ex=None):
        self._store[key] = value
        
    def delete(self, key):
        self._store.pop(key, None)
        
    def lock(self, name, timeout=10, blocking=False):
        return MockLock()


class MockLock:
    def acquire(self):
        return True
    def release(self):
        return True
