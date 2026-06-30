import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger("api.helpers")

class FinancialParserHelper:
    """
    Helper utilitario del dominio para formateo numérico, conversión y normalización de fechas.
    Completamente puro y libre de dependencias de infraestructura.
    """

    @staticmethod
    def _coerce_text(value: Any) -> str:
        return str(value).strip()
    
    @staticmethod
    def parse_float(value: Any, default: float = 0.0) -> float:
        """Parsea de manera segura strings complejos con formato financiero a decimal float (ej: '1.250,50')."""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
            
        try:
            cleaned = FinancialParserHelper._coerce_text(value).replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"No se pudo parsear el valor a float: {value}. Retornando default: {default}")
            return default

    @staticmethod
    def parse_int(value: Any, default: int = 0) -> int:
        """Parsea strings a enteros manejando caracteres extraños."""
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
            
        try:
            cleaned = FinancialParserHelper._coerce_text(value).split(".")[0].replace(",", "")
            return int(cleaned)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def parse_fecha(value: Any) -> datetime:
        """Normaliza múltiples tipos de formatos de fecha a un objeto datetime nativo."""
        if isinstance(value, datetime):
            return value
        if not value:
            return datetime.utcnow()

        val_str = str(value).strip()
        
        # Formatos comunes de parsing
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue

        logger.debug(f"Formato de fecha no identificado de forma estándar: {value}. Se asume UTC actual.")
        return datetime.utcnow()
