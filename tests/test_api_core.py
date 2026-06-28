import pytest
from src_python.domain.helpers.financial_parser_helper import FinancialParserHelper
from src_python.domain.models import ResourceModel
from src_python.application.get_resources_use_case import GetResourcesUseCase

# Clases Mock rápidas para testing aislado sin Redis o DB
class MockRepository:
    def fetch_all(self, category=None):
        return [
            ResourceModel(
                id="test_01",
                name="Servicios de Testeo",
                category="Pruebas",
                properties={}
            )
        ]
    def fetch_by_id(self, id):
         return None
    def save(self, res):
         return True


class MockCache:
    def get(self, key):
         return None
    def set(self, key, val, timeout=30):
         pass
    def delete(self, key):
         pass


def test_financial_parser_helper_float():
    """Valida que el Parser Helper de Dominio procese correctamente decimales venezolanos y americanos."""
    assert FinancialParserHelper.parse_float("1.250,75") == 1250.75
    assert FinancialParserHelper.parse_float("100,5") == 100.5
    assert FinancialParserHelper.parse_float("450") == 450.0
    assert FinancialParserHelper.parse_float(None) == 0.0


def test_financial_parser_helper_int():
    """Valida que el Parser Helper de Dominio convierta sin errores a enteros."""
    assert FinancialParserHelper.parse_int("1,500") == 1500
    assert FinancialParserHelper.parse_int(78.9) == 78


def test_get_resources_use_case():
    """Valida la correcta coordinación del Caso de Uso entregando salidas mapeadas."""
    use_case = GetResourcesUseCase(MockRepository(), MockCache())
    result = use_case.execute()
    
    assert len(result) == 1
    assert result[0]["id"] == "test_01"
    assert result[0]["category"] == "Pruebas"
