import logging
import uuid
from typing import Any, Dict, List, Optional

from ..domain.emergency_models import (
    EmergencyZoneModel,
    EmergencyZoneFilters,
    ZoneStatus,
    KNOWN_NEEDS,
)
from ..domain.emergency_repository_ports import IEmergencyZoneRepository

logger = logging.getLogger("api.application.emergency")

SOURCE_CATALOG = [
    {
        "name": "Discord - Coordinación Voluntarios VE",
        "type": "discord",
        "description": "Canal comunitario para reportes y coordinación de ayuda.",
    },
    {
        "name": "WhatsApp - Red de Apoyo Local",
        "type": "whatsapp",
        "description": "Grupos vecinales para reportar necesidades por zona.",
    },
    {
        "name": "Formulario manual",
        "type": "manual",
        "description": "Registro directo por operadores del equipo de respuesta.",
    },
    {
        "name": "API pública",
        "type": "public_api",
        "description": "Fuentes abiertas de datos geográficos o institucionales.",
    },
    {
        "name": "Redes sociales",
        "type": "social_media",
        "description": "Publicaciones públicas monitoreadas en X, Instagram o Facebook.",
    },
]


def _serialize_zone(zone: EmergencyZoneModel) -> Dict[str, Any]:
    return {
        "id": zone.id,
        "state": zone.state,
        "municipality": zone.municipality,
        "sector": zone.sector,
        "description": zone.description,
        "needs": zone.needs,
        "status": zone.status.value,
        "attended": zone.attended,
        "source_name": zone.source_name,
        "source_type": zone.source_type.value,
        "source_url": zone.source_url,
        "latitude": zone.latitude,
        "longitude": zone.longitude,
        "created_at": zone.created_at.isoformat(),
        "updated_at": zone.updated_at.isoformat(),
    }


class EmergencyUseCase:
    """Casos de uso del módulo Emergency: zonas, necesidades, fuentes y resumen."""

    def __init__(self, repository: IEmergencyZoneRepository):
        self.repository = repository

    def list_zones(self, filters: Optional[EmergencyZoneFilters] = None) -> List[Dict[str, Any]]:
        zones = self.repository.fetch_all(filters)
        return [_serialize_zone(z) for z in zones]

    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        zone = self.repository.fetch_by_id(zone_id)
        return _serialize_zone(zone) if zone else None

    def create_zone(self, data: Dict[str, Any]) -> Dict[str, Any]:
        zone_id = f"zone_{uuid.uuid4().hex[:8]}"
        zone = EmergencyZoneModel(id=zone_id, **data)
        saved = self.repository.save(zone)
        logger.info("Zona de emergencia creada: %s (%s, %s)", saved.id, saved.state, saved.municipality)
        return _serialize_zone(saved)

    def update_zone_status(self, zone_id: str, status: ZoneStatus) -> Optional[Dict[str, Any]]:
        updated = self.repository.update_status(zone_id, status)
        if updated:
            logger.info("Estado de zona %s actualizado a %s", zone_id, status.value)
            return _serialize_zone(updated)
        return None

    def get_needs_summary(self) -> Dict[str, Any]:
        zones = self.repository.fetch_all()
        needs_by_type: Dict[str, int] = {need: 0 for need in KNOWN_NEEDS}
        zones_with_need: Dict[str, List[str]] = {need: [] for need in KNOWN_NEEDS}

        for zone in zones:
            for need in zone.needs:
                normalized = need.lower().strip()
                if normalized in needs_by_type:
                    needs_by_type[normalized] += 1
                    zones_with_need[normalized].append(zone.id)

        critical_needs = sorted(
            [need for need, count in needs_by_type.items() if count > 0],
            key=lambda n: needs_by_type[n],
            reverse=True,
        )

        return {
            "needs_by_type": needs_by_type,
            "critical_needs": critical_needs[:5],
            "zones_per_need": {k: v for k, v in zones_with_need.items() if v},
            "total_active_zones": len(zones),
            "note": "Resumen calculado en memoria. No persistente entre reinicios.",
        }

    def get_sources(self) -> List[Dict[str, Any]]:
        zones = self.repository.fetch_all()
        active_sources: Dict[str, Dict[str, Any]] = {}

        for source in SOURCE_CATALOG:
            active_sources[source["type"]] = {**source, "zones_reported": 0}

        for zone in zones:
            key = zone.source_type.value
            if key not in active_sources:
                active_sources[key] = {
                    "name": zone.source_name,
                    "type": key,
                    "description": "Fuente registrada desde reportes de zona.",
                    "zones_reported": 0,
                }
            active_sources[key]["zones_reported"] += 1

        return list(active_sources.values())

    def get_summary(self) -> Dict[str, Any]:
        zones = self.repository.fetch_all()
        needs_summary = self.get_needs_summary()

        zones_by_state: Dict[str, int] = {}
        for zone in zones:
            zones_by_state[zone.state] = zones_by_state.get(zone.state, 0) + 1

        return {
            "total_zones": len(zones),
            "zones_needing_attention": sum(
                1 for z in zones if z.status in (ZoneStatus.NEEDS_ATTENTION, ZoneStatus.REPORTED)
            ),
            "zones_in_progress": sum(1 for z in zones if z.status == ZoneStatus.IN_PROGRESS),
            "zones_attended": sum(
                1 for z in zones if z.attended or z.status in (ZoneStatus.ATTENDED, ZoneStatus.RESOLVED)
            ),
            "critical_needs": needs_summary["critical_needs"],
            "needs_by_type": needs_summary["needs_by_type"],
            "zones_by_state": zones_by_state,
            "note": "Datos mock/in-memory. No incluye información personal ni persistencia real.",
        }
