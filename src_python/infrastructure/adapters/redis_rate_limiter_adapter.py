import time
import logging
import redis
from ...domain.repository_ports import IRateLimiter
from ..config import settings

logger = logging.getLogger("api.infrastructure")

class RedisRateLimiterAdapter(IRateLimiter):
    """Adaptador de Infraestructura para Limitar cuotas de peticiones mediante algoritmo de Sliding Window."""
    def __init__(self):
        if not getattr(settings, "USE_REDIS", True):
            logger.info("Redis desactivado por configuración. Rate limiter en modo permisivo local.")
            self.client = None
            self._available = False
            return

        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_RATE_LIMIT_DB,
                socket_connect_timeout=2
            )
            self.client.ping()
            self._available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self._available = False

    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        if not self._available:
            # Fail-safe: si el servidor Redis de contingencia falla, permitir peticiones temporalmente
            return True
            
        try:
            current_time = time.time()
            clean_before = current_time - window
            key = f"rate_limit:{identifier}"
            
            # Utilizar pipeline multi para consistencia atómica
            pipe = self.client.pipeline()
            pipe.zremrangebyscore(key, 0, clean_before)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()
            
            peticiones_realizadas = results[2]
            return peticiones_realizadas <= limit
        except Exception as e:
            logger.error(f"Excepción en el adaptador de Rate Limit Redis: {e}")
            return True
