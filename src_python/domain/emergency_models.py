from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ZoneStatus(str, Enum):
    REPORTED = "reported"
    NEEDS_ATTENTION = "needs_attention"
    IN_PROGRESS = "in_progress"
    ATTENDED = "attended"
    RESOLVED = "resolved"


class SourceType(str, Enum):
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    PUBLIC_API = "public_api"
    MANUAL = "manual"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


KNOWN_NEEDS = [
    "agua",
    "comida",
    "medicinas",
    "ropa",
    "refugio",
    "transporte",
    "atención médica",
    "maquinaria",
    "voluntarios",
]


class EmergencyZoneModel(BaseModel):
    id: str = Field(..., description="Identificador único de la zona")
    state: str = Field(..., min_length=2, description="Estado de Venezuela")
    municipality: str = Field(..., min_length=2, description="Municipio")
    sector: Optional[str] = Field(None, description="Sector o zona general (sin dirección exacta)")
    description: str = Field(..., min_length=5, description="Descripción de la situación")
    needs: List[str] = Field(default_factory=list, description="Necesidades reportadas")
    status: ZoneStatus = Field(default=ZoneStatus.REPORTED)
    attended: bool = Field(default=False)
    source_name: str = Field(..., min_length=2)
    source_type: SourceType
    source_url: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmergencyZoneFilters(BaseModel):
    state: Optional[str] = None
    municipality: Optional[str] = None
    status: Optional[ZoneStatus] = None
    attended: Optional[bool] = None
    need: Optional[str] = None
