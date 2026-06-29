from typing import List, Optional

from fastapi import HTTPException, status

from ....domain.emergency_models import EmergencyZoneFilters, ZoneStatus
from ...container import container
from ..schemas.emergency_schemas import (
    EmergencyZoneCreateSchema,
    EmergencyZoneStatusUpdateSchema,
    EmergencyZoneResponseSchema,
)


class EmergencyController:
    """Controlador HTTP del módulo Emergency."""

    @staticmethod
    def list_zones(
        state: Optional[str] = None,
        municipality: Optional[str] = None,
        zone_status: Optional[ZoneStatus] = None,
        attended: Optional[bool] = None,
        need: Optional[str] = None,
    ) -> List[dict]:
        filters = EmergencyZoneFilters(
            state=state,
            municipality=municipality,
            status=zone_status,
            attended=attended,
            need=need,
        )
        return container.emergency_use_case.list_zones(filters)

    @staticmethod
    def get_zone(zone_id: str) -> dict:
        zone = container.emergency_use_case.get_zone(zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zona '{zone_id}' no encontrada.",
            )
        return zone

    @staticmethod
    def create_zone(payload: EmergencyZoneCreateSchema) -> dict:
        return container.emergency_use_case.create_zone(payload.model_dump())

    @staticmethod
    def update_zone_status(zone_id: str, payload: EmergencyZoneStatusUpdateSchema) -> dict:
        updated = container.emergency_use_case.update_zone_status(zone_id, payload.status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zona '{zone_id}' no encontrada.",
            )
        return updated

    @staticmethod
    def get_needs_summary() -> dict:
        return container.emergency_use_case.get_needs_summary()

    @staticmethod
    def get_sources() -> List[dict]:
        return container.emergency_use_case.get_sources()

    @staticmethod
    def get_summary() -> dict:
        return container.emergency_use_case.get_summary()
