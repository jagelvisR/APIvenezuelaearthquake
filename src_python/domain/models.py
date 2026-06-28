from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResourceModel(BaseModel):
    id: str = Field(..., description="Identificador único del recurso")
    name: str = Field(..., description="Nombre descriptivo")
    description: Optional[str] = Field(None, description="Descripción ampliada")
    category: str = Field(..., description="Categoría o tipo de recurso")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadatos dinámicos")


class RequestPayload(BaseModel):
    message: str = Field(..., min_length=2, description="Mensaje de consulta o petición de usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión para rastrear la interacción")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros de filtrado")
