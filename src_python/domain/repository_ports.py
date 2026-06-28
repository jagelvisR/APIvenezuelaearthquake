from abc import ABC, abstractmethod
from typing import List, Optional, Any
from .models import ResourceModel

class IResourceRepository(ABC):
    @abstractmethod
    def fetch_all(self, category: Optional[str] = None) -> List[ResourceModel]:
        """Recuperar todos los recursos bajo filtros opcionales."""
        pass

    @abstractmethod
    def fetch_by_id(self, resource_id: str) -> Optional[ResourceModel]:
        """Obtener un recurso según su identificador único."""
        pass

    @abstractmethod
    def save(self, resource: ResourceModel) -> bool:
        """Almacenar o actualizar el recurso en el almacenamiento persistente."""
        pass


class ICacheService(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        """Recuperar valor de la caché."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        """Almacena un par clave-valor con expiración dinámica."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remueve manualmente una clave de la caché."""
        pass


class IRateLimiter(ABC):
    @abstractmethod
    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        """Verifica si un cliente supera el límite de peticiones (Rate Limit)."""
        pass
