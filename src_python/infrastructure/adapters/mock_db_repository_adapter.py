from typing import List, Optional
from datetime import datetime
from ...domain.models import ResourceModel
from ...domain.repository_ports import IResourceRepository

class MockDBRepositoryAdapter(IResourceRepository):
    """
    Adaptador de repositorio simulado (Mock / In-Memory Database).
    En producción, este archivo importará SQLAlchemy, Tortoise o SQLModel para interactuar con PostgreSQL.
    """
    def __init__(self):
        self._database = [
            ResourceModel(
                id="res_01",
                name="Servicio de Autenticación Central",
                description="Clúster SSO integrado con soporte JWT.",
                category="Sistemas",
                created_at=datetime.utcnow(),
                properties={"sla": "99.99%", "owner": "DevOps Team"}
            ),
            ResourceModel(
                id="res_02",
                name="Motor de Predicciones AI",
                description="Servicio conversacional de inferencia inteligente.",
                category="IA",
                created_at=datetime.utcnow(),
                properties={"model": "deepseek-reasoner", "api_calls_quota": 5000}
            ),
            ResourceModel(
                id="res_03",
                name="Base de Datos Analítica Principal",
                description="Data warehouse analítico estructurado en PostgreSQL.",
                category="Bases de Datos",
                created_at=datetime.utcnow(),
                properties={"engine": "PostgreSQL 16", "backup_policy": "Daily"}
            )
        ]

    def fetch_all(self, category: Optional[str] = None) -> List[ResourceModel]:
        if category:
            return [res for res in self._database if res.category.lower() == category.lower()]
        return self._database

    def fetch_by_id(self, resource_id: str) -> Optional[ResourceModel]:
        for res in self._database:
            if res.id == resource_id:
                return res
        return None

    def save(self, resource: ResourceModel) -> bool:
        # Remover si ya existe para simular un UPSERT
        self._database = [res for res in self._database if res.id != resource.id]
        self._database.append(resource)
        return True
