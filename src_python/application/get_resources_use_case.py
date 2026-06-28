import logging
from typing import List, Optional, Dict, Any
from ..domain.models import ResourceModel
from ..domain.repository_ports import IResourceRepository, ICacheService

logger = logging.getLogger("api.application")

class GetResourcesUseCase:
    """
    Caso de Uso: Obtener Recursos con soporte de Caché Proactivo.
    Coordina la obtención de datos a través de los puertos del dominio.
    """
    def __init__(self, repository: IResourceRepository, cache_service: ICacheService):
        self.repository = repository
        self.cache_service = cache_service

    def execute(self, category: Optional[str] = None, refresh: bool = False) -> List[Dict[str, Any]]:
        cache_key = f"resources:list:{category or 'all'}"
        
        # 1. Si no se fuerza el refrescado, intentar leer de la Caché (Redis)
        if not refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data:
                logger.info(f"⚡ Caché recuperado con éxito para la clave de consulta: {cache_key}")
                return cached_data

        # 2. Obtener datos reales mediante Adaptador de Repositorio (Infraestructura)
        logger.info(f"🔍 Buscando recursos frescos en almacenamiento. Categoría: {category}")
        resources: List[ResourceModel] = self.repository.fetch_all(category)
        
        # 3. Mapear datos a diccionarios limpios
        serialized_data = []
        for resource in resources:
            serialized_data.append({
                "id": resource.id,
                "name": resource.name,
                "description": resource.description,
                "category": resource.category,
                "created_at": resource.created_at.isoformat(),
                "properties": resource.properties
            })

        # 4. Guardar en Caché de Redis por 120 segundos
        try:
            self.cache_service.set(cache_key, serialized_data, timeout=120)
            logger.info(f"💾 Clave de caché actualizada exitosamente: {cache_key}")
        except Exception as e:
            logger.error(f"⚠️ Error al guardar información en caché: {e}")

        return serialized_data
