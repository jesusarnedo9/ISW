"""Pruebas de integración de la API REST de la interfaz web."""

import pytest
from datetime import datetime, timedelta
import app as flask_app_module


@pytest.fixture
def client():
    flask_app_module.app.config["TESTING"] = True
    # Resetear servicio antes de cada test
    flask_app_module.servicio = flask_app_module.crear_servicio_inicial()
    with flask_app_module.app.test_client() as client:
        yield client


def test_api_config(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.get_json()
    assert "actividades" in data
    assert len(data["actividades"]) == 4
    assert "feriados" in data
    assert "turnos_horas" in data


def test_api_cupos_fecha_valida(client):
    maniana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    res = client.get(f"/api/cupos?fecha={maniana}")
    assert res.status_code == 200
    data = res.get_json()
    assert "turnos" in data
    assert "parque_abierto" in data


def test_api_inscribir_exitoso(client):
    # Martes 20/10/2026 10:00 con simulación de tiempo a las 08:00
    payload = {
        "actividad": "Tirolesa",
        "fecha": "2026-10-20",
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Ana Pérez", "dni": 30123456, "edad": 25, "talla": "M"}
        ],
        "acepta_terminos": True,
        "id_terminos_aceptados": "TYC-TIRO-v1",
        "email": "ana@example.com",
        "ahora": "2026-10-20T08:00:00",
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["exito"] is True
    assert "numero_orden" in data["confirmacion"]
    assert len(data["confirmacion"]["codigos_qr"]) == 1
    assert data["confirmacion"]["codigos_qr"][0].startswith("data:image/svg+xml;base64,")


def test_api_inscribir_sin_aceptar_terminos(client):
    payload = {
        "actividad": "Tirolesa",
        "fecha": "2026-10-20",
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Ana Pérez", "dni": 30123456, "edad": 25, "talla": "M"}
        ],
        "acepta_terminos": False,
        "email": "ana@example.com",
        "ahora": "2026-10-20T08:00:00",
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 403
    data = res.get_json()
    assert data["exito"] is False
    assert data["tipo_error"] == "TerminosNoAceptados"


def test_api_correos_enviados(client):
    # Primero hacemos una inscripción
    payload = {
        "actividad": "Safari",
        "fecha": "2026-10-20",
        "hora": "11:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Carlos Gómez", "dni": 28999888, "edad": 30}
        ],
        "acepta_terminos": True,
        "id_terminos_aceptados": "TYC-SAF-v1",
        "email": "carlos@example.com",
        "ahora": "2026-10-20T08:00:00",
    }
    client.post("/api/inscribir", json=payload)

    res = client.get("/api/correos")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_enviados"] >= 1
    assert data["correos"][0]["destinatario"] == "carlos@example.com"
