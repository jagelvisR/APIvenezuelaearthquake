import functools
from fastapi import APIRouter, Security, HTTPException, status, Query, Request
from typing import Optional, List, Dict, Any

from ...domain.models import ResourceModel, RequestPayload
from ...domain.helpers.financial_parser_helper import FinancialParserHelper
from ..container import container

# --- Decorador de Rate Limit para FastAPI ---
def rate_limit(limit: int, window: int = 60):
    """
    Decorador para aplicar límites de peticiones (Rate Limiting) en endpoints de FastAPI de forma limpia.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return func(*args, **kwargs)
                
            client_ip = request.client.host if request.client else "unknown_ip"
            identifier = f"{func.__name__}:{client_ip}"
            
            allowed = container.rate_limiter.is_allowed(identifier, limit=limit, window=window)
            if not allowed:
                 raise HTTPException(
                     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                     detail=f"Se ha superado el límite de autorizaciones para este recurso (máximo {limit} peticiones por {window} segundos)."
                 )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Creamos el Router simulando un archivo de rutas de Laravel.
# Permite agrupar los endpoints bajo un prefijo unificado y encapsular lógica limpia.
router = APIRouter(prefix="/v1")

@router.get("/status", tags=["Utility"])
def get_root_status():
    """Endpoint público informativo para validación de salud de la API (Health Probe)."""
    return {
        "status": "healthy",
        "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
        "version": "1.0.0"
    }


@router.get("/resources", tags=["Resources"])
@rate_limit(limit=20, window=60)
def get_resources_endpoint(
    request: Request,
    category: Optional[str] = Query(None, description="Categoría para filtrar recursos"),
    force_refresh: bool = Query(False, alias="refresh", description="Forzar lectura omitiendo la caché de Redis"),
):
    """
    Endpoint Seguro con Rate-Limit y Caché Dinámico de alto rendimiento.
    Retorna el listado de recursos computados y administrados por el Caso de Uso.
    """
    # --- Rate Limit: Límite del Endpoint (20 peticiones por minuto por dirección IP) ---
    client_ip = request.client.host if request.client else "unknown_ip"
    rate_limit_id = f"endpoint:get_resources:{client_ip}"
    allowed = container.rate_limiter.is_allowed(rate_limit_id, limit=20, window=60)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Se ha superado el límite de peticiones autorizadas por minuto. Intente de nuevo en breve."
        )

    # Executar la lógica de negocio a través del contenedor
    return container.get_resources_use_case.execute(category=category, refresh=force_refresh)


@router.post("/resources/parse-value", tags=["Helpers"])
def execute_financial_parsing(payload: Dict[str, Any]):
    """Endpoint de ejemplo que demuestra el uso de Helpers de Formateo de Datos Puro de la capa Domain."""
    raw_value = payload.get("value")
    return {
        "original": raw_value,
        "parsed_float": FinancialParserHelper.parse_float(raw_value),
        "parsed_int": FinancialParserHelper.parse_int(raw_value),
        "parsed_fecha": FinancialParserHelper.parse_fecha(payload.get("fecha")).isoformat()
    }
