from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from ....domain.emergency_models import ZoneStatus, SourceType, KNOWN_NEEDS


class EmergencyZoneCreateSchema(BaseModel):
    state: str = Field(..., min_length=2, examples=["Lara"])
    municipality: str = Field(..., min_length=2, examples=["Iribarren"])
    sector: Optional[str] = Field(None, examples=["Zona norte"])
    description: str = Field(..., min_length=5, examples=["Falta agua potable y refugio temporal."])
    needs: List[str] = Field(default_factory=list, examples=[["agua", "comida"]])
    status: ZoneStatus = Field(default=ZoneStatus.REPORTED)
    attended: bool = False
    source_name: str = Field(..., min_length=2, examples=["Discord - Coordinación"])
    source_type: SourceType
    source_url: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("needs")
    @classmethod
    def validate_needs(cls, values: List[str]) -> List[str]:
        if not values:
            return values
        normalized_known = {n.lower() for n in KNOWN_NEEDS}
        for need in values:
            if need.lower().strip() not in normalized_known:
                raise ValueError(
                    f"Necesidad '{need}' no reconocida. Valores permitidos: {', '.join(KNOWN_NEEDS)}"
                )
        return [n.lower().strip() for n in values]


class EmergencyZoneStatusUpdateSchema(BaseModel):
    status: ZoneStatus = Field(..., examples=["in_progress"])


class EmergencyZoneResponseSchema(BaseModel):
    id: str
    state: str
    municipality: str
    sector: Optional[str]
    description: str
    needs: List[str]
    status: str
    attended: bool
    source_name: str
    source_type: str
    source_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: str
    updated_at: str
