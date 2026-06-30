import os

os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from fastapi.testclient import TestClient

from src_python.domain.emergency_models import EmergencyZoneFilters, ZoneStatus, SourceType
from src_python.application.emergency_use_case import EmergencyUseCase
from src_python.infrastructure.adapters.mock_emergency_zone_repository_adapter import (
    MockEmergencyZoneRepositoryAdapter,
)
from src_python.infrastructure.fastapi_app import app


@pytest.fixture
def emergency_use_case():
    return EmergencyUseCase(MockEmergencyZoneRepositoryAdapter())


@pytest.fixture
def client():
    return TestClient(app)


def test_list_zones_returns_mock_data(emergency_use_case):
    zones = emergency_use_case.list_zones()
    assert len(zones) >= 5
    assert zones[0]["state"]
    assert "needs" in zones[0]


def test_list_zones_filter_by_state(emergency_use_case):
    zones = emergency_use_case.list_zones(EmergencyZoneFilters(state="Lara"))
    assert len(zones) == 1
    assert zones[0]["state"] == "Lara"


def test_list_zones_filter_by_need(emergency_use_case):
    zones = emergency_use_case.list_zones(EmergencyZoneFilters(need="agua"))
    assert all("agua" in z["needs"] for z in zones)
    assert len(zones) >= 2


def test_get_zone_by_id(emergency_use_case):
    zone = emergency_use_case.get_zone("zone_01")
    assert zone is not None
    assert zone["id"] == "zone_01"
    assert zone["municipality"] == "Iribarren"


def test_get_zone_not_found(emergency_use_case):
    assert emergency_use_case.get_zone("zone_inexistente") is None


def test_create_zone(emergency_use_case):
    payload = {
        "state": "Zulia",
        "municipality": "Maracaibo",
        "sector": "Sector costero",
        "description": "Reporte de prueba sin datos personales sensibles.",
        "needs": ["agua", "transporte"],
        "status": ZoneStatus.REPORTED,
        "attended": False,
        "source_name": "Formulario manual",
        "source_type": SourceType.MANUAL,
    }
    created = emergency_use_case.create_zone(payload)
    assert created["id"].startswith("zone_")
    assert created["state"] == "Zulia"
    assert "agua" in created["needs"]


def test_update_zone_status(emergency_use_case):
    updated = emergency_use_case.update_zone_status("zone_03", ZoneStatus.IN_PROGRESS)
    assert updated is not None
    assert updated["status"] == "in_progress"
    assert updated["attended"] is False


def test_update_zone_status_sets_attended_when_resolved(emergency_use_case):
    updated = emergency_use_case.update_zone_status("zone_01", ZoneStatus.RESOLVED)
    assert updated["status"] == "resolved"
    assert updated["attended"] is True


def test_get_needs_summary(emergency_use_case):
    summary = emergency_use_case.get_needs_summary()
    assert "needs_by_type" in summary
    assert summary["needs_by_type"]["agua"] >= 1
    assert "critical_needs" in summary


def test_get_sources(emergency_use_case):
    sources = emergency_use_case.get_sources()
    types = {s["type"] for s in sources}
    assert "discord" in types
    assert "manual" in types


def test_get_summary(emergency_use_case):
    summary = emergency_use_case.get_summary()
    assert summary["total_zones"] >= 5
    assert "zones_by_state" in summary
    assert "Lara" in summary["zones_by_state"]


def test_http_list_emergency_zones(client):
    response = client.get("/api/v1/emergency/zones")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_http_get_emergency_zone_detail(client):
    response = client.get("/api/v1/emergency/zones/zone_01")
    assert response.status_code == 200
    assert response.json()["id"] == "zone_01"


def test_http_create_emergency_zone(client):
    response = client.post(
        "/api/v1/emergency/zones",
        json={
            "state": "Táchira",
            "municipality": "San Cristóbal",
            "description": "Zona con necesidad de refugio temporal reportada por operadores.",
            "needs": ["refugio"],
            "source_name": "Formulario manual",
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    assert response.json()["state"] == "Táchira"


def test_http_patch_zone_status(client):
    response = client.patch(
        "/api/v1/emergency/zones/zone_02/status",
        json={"status": "attended"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "attended"


def test_http_emergency_summary(client):
    response = client.get("/api/v1/emergency/summary")
    assert response.status_code == 200
    body = response.json()
    assert "total_zones" in body
    assert "needs_by_type" in body


def test_http_create_zone_rejects_unknown_need(client):
    response = client.post(
        "/api/v1/emergency/zones",
        json={
            "state": "Lara",
            "municipality": "Iribarren",
            "description": "Reporte con necesidad inválida para validación.",
            "needs": ["internet"],
            "source_name": "Manual",
            "source_type": "manual",
        },
    )
    assert response.status_code == 422
