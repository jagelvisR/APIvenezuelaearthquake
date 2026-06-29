from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Request
from ...domain.helpers.financial_parser_helper import FinancialParserHelper
from ..container import container

class ResourcesController:
    """
    Controlador de Recursos que maneja la lógica HTTP de entrada
    y delega las ejecuciones a los casos de uso correspondientes.
    """
    @staticmethod
    def get_root_status() -> Dict[str, str]:
        """Endpoint público informativo de salud."""
        return {
            "status": "healthy",
            "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
            "version": "1.0.0"
        }

    @staticmethod
    def get_resources_endpoint(
        request: Request,
        category: Optional[str] = None,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Consigue los recursos a través del Caso de Uso (con límites y caché)."""
        try:
            
            # Delegamos a la capa de Aplicación
            return container.get_resources_use_case.execute(category=category, refresh=force_refresh)
        except HTTPException as http_ex:
            # Re-lanzamos excepciones HTTP para que FastAPI las maneje
            raise http_ex

    @staticmethod
    def execute_financial_parsing(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta Parseo Financiero del Dominio."""
        raw_value = payload.get("value")
        return {
            "original": raw_value,
            "parsed_float": FinancialParserHelper.parse_float(raw_value),
            "parsed_int": FinancialParserHelper.parse_int(raw_value),
            "parsed_fecha": FinancialParserHelper.parse_fecha(payload.get("fecha")).isoformat()
        }
