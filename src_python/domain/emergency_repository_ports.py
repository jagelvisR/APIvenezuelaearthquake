from abc import ABC, abstractmethod
from typing import List, Optional

from .emergency_models import EmergencyZoneModel, EmergencyZoneFilters, ZoneStatus


class IEmergencyZoneRepository(ABC):
    @abstractmethod
    def fetch_all(self, filters: Optional[EmergencyZoneFilters] = None) -> List[EmergencyZoneModel]:
        """Recuperar zonas con filtros opcionales."""
        pass

    @abstractmethod
    def fetch_by_id(self, zone_id: str) -> Optional[EmergencyZoneModel]:
        """Obtener una zona por su identificador."""
        pass

    @abstractmethod
    def save(self, zone: EmergencyZoneModel) -> EmergencyZoneModel:
        """Crear o actualizar una zona."""
        pass

    @abstractmethod
    def update_status(self, zone_id: str, status: ZoneStatus) -> Optional[EmergencyZoneModel]:
        """Actualizar el estado operativo de una zona."""
        pass
