from datetime import datetime, timedelta
from typing import List, Optional

from ...domain.emergency_models import (
    EmergencyZoneModel,
    EmergencyZoneFilters,
    ZoneStatus,
    SourceType,
)
from ...domain.emergency_repository_ports import IEmergencyZoneRepository


def _build_initial_zones() -> List[EmergencyZoneModel]:
    now = datetime.utcnow()
    return [
        EmergencyZoneModel(
            id="zone_01",
            state="Lara",
            municipality="Iribarren",
            sector="Zona norte de Barquisimeto",
            description="Edificios con daños estructurales leves. Familias en refugios temporales sin acceso estable a agua potable.",
            needs=["agua", "comida", "refugio"],
            status=ZoneStatus.NEEDS_ATTENTION,
            attended=False,
            source_name="Discord - Coordinación Voluntarios VE",
            source_type=SourceType.DISCORD,
            source_url="https://discord.com/channels/ejemplo",
            latitude=10.0739,
            longitude=-69.3238,
            created_at=now - timedelta(hours=18),
            updated_at=now - timedelta(hours=2),
        ),
        EmergencyZoneModel(
            id="zone_02",
            state="Yaracuy",
            municipality="San Felipe",
            sector="Sector La Esperanza",
            description="Escuela usada como albergue. Falta insumos médicos básicos y personal de apoyo.",
            needs=["medicinas", "atención médica", "voluntarios"],
            status=ZoneStatus.IN_PROGRESS,
            attended=False,
            source_name="WhatsApp - Red de Apoyo Local",
            source_type=SourceType.WHATSAPP,
            latitude=10.3400,
            longitude=-68.7317,
            created_at=now - timedelta(hours=30),
            updated_at=now - timedelta(hours=5),
        ),
        EmergencyZoneModel(
            id="zone_03",
            state="Carabobo",
            municipality="Valencia",
            sector="Sur de Valencia",
            description="Vías laterales bloqueadas por escombros. Comunidades aisladas reportan escasez de alimentos.",
            needs=["comida", "transporte", "maquinaria"],
            status=ZoneStatus.REPORTED,
            attended=False,
            source_name="Redes sociales",
            source_type=SourceType.SOCIAL_MEDIA,
            source_url="https://x.com/ejemplo/reporte",
            latitude=10.1621,
            longitude=-68.0077,
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=8),
        ),
        EmergencyZoneModel(
            id="zone_04",
            state="Distrito Capital",
            municipality="Libertador",
            sector="Zona este",
            description="Punto de acopio activo. Se recibió ayuda inicial pero aún faltan medicinas y ropa.",
            needs=["medicinas", "ropa"],
            status=ZoneStatus.ATTENDED,
            attended=True,
            source_name="Formulario manual",
            source_type=SourceType.MANUAL,
            latitude=10.4806,
            longitude=-66.9036,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=12),
        ),
        EmergencyZoneModel(
            id="zone_05",
            state="Falcón",
            municipality="Miranda",
            sector="Coro histórico",
            description="Zona patrimonial con riesgo de derrumbes. Se requiere evaluación técnica y refugio temporal.",
            needs=["refugio", "voluntarios", "maquinaria"],
            status=ZoneStatus.NEEDS_ATTENTION,
            attended=False,
            source_name="API pública",
            source_type=SourceType.PUBLIC_API,
            source_url="https://ejemplo.gov.ve/datos",
            latitude=11.4045,
            longitude=-69.6737,
            created_at=now - timedelta(hours=14),
            updated_at=now - timedelta(hours=3),
        ),
        EmergencyZoneModel(
            id="zone_06",
            state="Portuguesa",
            municipality="Guanare",
            sector="Periferia urbana",
            description="Lluvias posteriores agravaron inundaciones. Bombeo de agua y transporte para evacuación.",
            needs=["agua", "transporte"],
            status=ZoneStatus.RESOLVED,
            attended=True,
            source_name="Discord - Coordinación Voluntarios VE",
            source_type=SourceType.DISCORD,
            latitude=9.0431,
            longitude=-69.7489,
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(hours=1),
        ),
    ]


class MockEmergencyZoneRepositoryAdapter(IEmergencyZoneRepository):
    """
    Repositorio mock en memoria para zonas de emergencia.
    Los datos se pierden al reiniciar el proceso.
    """

    def __init__(self):
        self._zones: List[EmergencyZoneModel] = _build_initial_zones()

    def _matches_filters(self, zone: EmergencyZoneModel, filters: EmergencyZoneFilters) -> bool:
        if filters.state and zone.state.lower() != filters.state.lower():
            return False
        if filters.municipality and zone.municipality.lower() != filters.municipality.lower():
            return False
        if filters.status and zone.status != filters.status:
            return False
        if filters.attended is not None and zone.attended != filters.attended:
            return False
        if filters.need:
            normalized_need = filters.need.lower().strip()
            zone_needs = [n.lower().strip() for n in zone.needs]
            if normalized_need not in zone_needs:
                return False
        return True

    def fetch_all(self, filters: Optional[EmergencyZoneFilters] = None) -> List[EmergencyZoneModel]:
        if not filters:
            return list(self._zones)
        return [z for z in self._zones if self._matches_filters(z, filters)]

    def fetch_by_id(self, zone_id: str) -> Optional[EmergencyZoneModel]:
        for zone in self._zones:
            if zone.id == zone_id:
                return zone
        return None

    def save(self, zone: EmergencyZoneModel) -> EmergencyZoneModel:
        existing_idx = next((i for i, z in enumerate(self._zones) if z.id == zone.id), None)
        if existing_idx is not None:
            self._zones[existing_idx] = zone
        else:
            self._zones.append(zone)
        return zone

    def update_status(self, zone_id: str, status: ZoneStatus) -> Optional[EmergencyZoneModel]:
        zone = self.fetch_by_id(zone_id)
        if not zone:
            return None
        updated = zone.model_copy(
            update={
                "status": status,
                "attended": status in (ZoneStatus.ATTENDED, ZoneStatus.RESOLVED),
                "updated_at": datetime.utcnow(),
            }
        )
        return self.save(updated)
