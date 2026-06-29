from typing import List, Optional

from fastapi import APIRouter, Query

from ...domain.emergency_models import ZoneStatus
from .controllers.emergency_controller import EmergencyController
from .schemas.emergency_schemas import (
    EmergencyZoneCreateSchema,
    EmergencyZoneStatusUpdateSchema,
    EmergencyZoneResponseSchema,
)

emergency_router = APIRouter(prefix="/emergency", tags=["Emergency"])


@emergency_router.get(
    "/zones",
    response_model=List[EmergencyZoneResponseSchema],
    summary="Listar zonas reportadas",
)
def list_emergency_zones(
    state: Optional[str] = Query(None, description="Filtrar por estado"),
    municipality: Optional[str] = Query(None, description="Filtrar por municipio"),
    status: Optional[ZoneStatus] = Query(None, description="Filtrar por estado operativo"),
    attended: Optional[bool] = Query(None, description="Filtrar por si fue atendida"),
    need: Optional[str] = Query(None, description="Filtrar zonas que reporten una necesidad"),
):
    return EmergencyController.list_zones(
        state=state,
        municipality=municipality,
        zone_status=status,
        attended=attended,
        need=need,
    )


@emergency_router.get(
    "/zones/{zone_id}",
    response_model=EmergencyZoneResponseSchema,
    summary="Detalle de una zona",
)
def get_emergency_zone(zone_id: str):
    return EmergencyController.get_zone(zone_id)


@emergency_router.post(
    "/zones",
    response_model=EmergencyZoneResponseSchema,
    status_code=201,
    summary="Crear reporte de zona",
)
def create_emergency_zone(payload: EmergencyZoneCreateSchema):
    return EmergencyController.create_zone(payload)


@emergency_router.patch(
    "/zones/{zone_id}/status",
    response_model=EmergencyZoneResponseSchema,
    summary="Actualizar estado de una zona",
)
def update_emergency_zone_status(zone_id: str, payload: EmergencyZoneStatusUpdateSchema):
    return EmergencyController.update_zone_status(zone_id, payload)


@emergency_router.get("/needs", summary="Resumen de necesidades agrupadas")
def get_emergency_needs():
    return EmergencyController.get_needs_summary()


@emergency_router.get("/sources", summary="Fuentes de información registradas")
def get_emergency_sources():
    return EmergencyController.get_sources()


@emergency_router.get("/summary", summary="Resumen general de emergencia")
def get_emergency_summary():
    return EmergencyController.get_summary()
