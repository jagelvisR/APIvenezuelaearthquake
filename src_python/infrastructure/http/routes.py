from fastapi import APIRouter, Query, Request, Security
from typing import Optional, Dict, Any

from .controllers.resources_controller import ResourcesController
from .rate_limiter_decorator import rate_limit

# Router HTTP actual del proyecto. Todo cuelga de `/api/v1` cuando se monta desde fastapi_app.py.
router = APIRouter(prefix="/v1")

# --- Endpoints de salud y recursos ---
@router.get("/status", tags=["Utility"])
def get_status():
    """Endpoint público informativo de salud."""
    return ResourcesController.get_root_status()

# `refresh=true` fuerza bypass de caché; el rate limit se aplica por IP y nombre de función.
@router.get("/resources", tags=["Resources"])
@rate_limit(limit=20, window=60)
def get_resources(
    request: Request,
    category: Optional[str] = Query(None, description="Categoría para filtrar recursos"),
    force_refresh: bool = Query(False, alias="refresh", description="Forzar lectura omitiendo la caché de Redis"),
):
    return ResourcesController.get_resources_endpoint(
        request=request,
        category=category,
        force_refresh=force_refresh
    )

@router.post("/resources/parse-value", tags=["Helpers"])
def execute_financial_parsing(payload: Dict[str, Any]):
    return ResourcesController.execute_financial_parsing(payload)
